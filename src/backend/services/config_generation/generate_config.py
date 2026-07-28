from collections import Counter, defaultdict
from dataclasses import dataclass, field
import copy
import logging
import re

from aerleon.lib import naming
from aerleon import api as aerleon_api
from django.contrib.auth.models import User

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.services.attribute_objects.get_address_objects import get_address_group_members
from backend.services.attribute_objects.get_service_objects import get_service_group_members
from backend.services.config_generation.platform_capabilities import vendor_supports
from backend.services.get import DJANGO_MODEL_MAPPING
from backend.utils.logger import set_up_logger
from constants import DIRECTION_CHOICES


logger = set_up_logger(__name__)

SHADING_WARNING_PATTERN = re.compile(r"^(?P<term>.+?) is shaded by (?P<shaded_by>.+)$")


@dataclass(frozen=True)
class GenerationDiagnostic:
    source: str
    level: str
    code: str
    message: str
    term_name: str | None = None
    shaded_by_name: str | None = None


@dataclass
class ConfigGenerationResult:
    config: dict | None
    warnings: list[GenerationDiagnostic] = field(default_factory=list)
    errors: list[GenerationDiagnostic] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


@dataclass
class RuleBuildResult:
    terms: list[dict]
    networks: dict[str, dict]
    services: dict[str, list[dict]]
    warnings: list[str] = field(default_factory=list)


class _AerleonLogCaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class PolicyRuleMember:
    """
    Represents a single object attached to a PolicyRule.
    Essentially a "Rule_match" from the ER diagram

    A member can be one of:
    - Address
    - AddressGroup
    - Service
    - ServiceGroup

    And it applies in one of the supported directions:
    - source
    - destination
    - reverse_source
    - reverse_destination
    - any
    """

    VALID_TYPES = {"address", "addressgroup", "service", "servicegroup"}

    def __init__(
        self,
        obj_type: str,
        direction: str,
        object: Address | AddressGroup | Service | ServiceGroup,
    ):
        normalized_type = obj_type.lower().strip()
        normalized_direction = direction.lower().strip()

        if normalized_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid obj_type: {obj_type}. Must be one of {sorted(self.VALID_TYPES)}")

        if normalized_direction not in DIRECTION_CHOICES:
            raise ValueError(f"Invalid direction: {direction}. Must be one of {DIRECTION_CHOICES}")

        expected_class = DJANGO_MODEL_MAPPING.get(normalized_type)
        if expected_class is None:
            raise ValueError(f"No Django model mapping found for obj_type '{normalized_type}'")

        if not isinstance(object, expected_class):
            raise TypeError(
                f"Object for obj_type '{normalized_type}' must be of type "
                f"{expected_class.__name__}, got {type(object).__name__}"
            )

        self.type = normalized_type
        self.direction = normalized_direction
        self.object = object

    def __repr__(self) -> str:
        return (
            f"PolicyRuleMember(type={self.type!r}, "
            f"direction={self.direction!r}, "
            f"object={getattr(self.object, 'name', self.object)!r})"
        )


class PolicyRule:
    """
    Represents a single logical rule in a policy.
    Basically a "Rule" from the ER diagram, but with all its RuleMatch objects converted into PolicyRuleMember objects.

    A PolicyRule has:
    - one action
    - one unique rule_sequence used for ordering in the filter
    - one or more PolicyRuleMember objects that define addresses/services/groups

    A PolicyRule normally builds a single Aerleon term, but may build multiple
    terms in the caveat case where protocol-specific port mappings differ and
    must be split to preserve semantics.
    """

    PORT_BASED_PROTOCOLS = {"tcp", "udp"}

    def __init__(
        self,
        actor: User,
        tenant_id: int,
        name: str,
        action: str,
        rule_sequence: int,
        members: list[PolicyRuleMember],
    ):
        if not name or not name.strip():
            raise ValueError("PolicyRule name cannot be empty")

        if not action or not action.strip():
            raise ValueError("PolicyRule action cannot be empty")

        if rule_sequence < 1:
            raise ValueError("rule_sequence must be >= 1")

        if members is None:
            raise ValueError("members cannot be None")

        if not members:
            raise ValueError("PolicyRule must contain at least one member")

        self.actor = actor
        self.tenant_id = tenant_id
        self.name = name.strip().replace(" ", "_")
        self.action = action.lower().strip()
        self.rule_sequence = rule_sequence
        self.members = members

    def rendered_term_name(self, suffix: str | None = None) -> str:
        """
        Render the final Aerleon term name, max 62 chars.
        If a suffix is provided, preserve it within the limit.
        """
        if suffix is None:
            return self.name[:62]

        suffix_part = f"-{suffix}"
        max_base_length = 62 - len(suffix_part)
        return f"{self.name[:max_base_length]}{suffix_part}"

    def build(self, vendor: str) -> RuleBuildResult:
        """
        Build Aerleon term(s) and required network/service definitions for this rule
        for a specific vendor/platform.

        Normally returns a single term. If protocol-specific port mappings differ
        across protocols, returns one term per protocol and emits a warning.
        """
        networks: dict[str, dict] = {}
        services: dict[str, list[dict]] = {}
        warnings: list[str] = []

        source_addresses: list[str] = []
        destination_addresses: list[str] = []
        reverse_source_addresses: list[str] = []
        reverse_destination_addresses: list[str] = []

        source_ports_by_protocol: dict[str, list[str]] = defaultdict(list)
        destination_ports_by_protocol: dict[str, list[str]] = defaultdict(list)
        reverse_source_ports_by_protocol: dict[str, list[str]] = defaultdict(list)
        reverse_destination_ports_by_protocol: dict[str, list[str]] = defaultdict(list)
        any_ports_by_protocol: dict[str, list[str]] = defaultdict(list)

        source_port_values_by_protocol: dict[str, list[str]] = defaultdict(list)
        destination_port_values_by_protocol: dict[str, list[str]] = defaultdict(list)
        reverse_source_port_values_by_protocol: dict[str, list[str]] = defaultdict(list)
        reverse_destination_port_values_by_protocol: dict[str, list[str]] = defaultdict(list)
        any_port_values_by_protocol: dict[str, list[str]] = defaultdict(list)

        all_protocols: set[str] = set()

        for member in self.members:
            match member.type:
                case "address":
                    self._add_address_definition(networks, member.object)
                    self._append_by_direction(
                        direction=member.direction,
                        source_list=source_addresses,
                        destination_list=destination_addresses,
                        reverse_source_list=reverse_source_addresses,
                        reverse_destination_list=reverse_destination_addresses,
                        value=member.object.name,
                    )

                case "addressgroup":
                    self._add_address_group_definition(networks, member.object)
                    self._append_by_direction(
                        direction=member.direction,
                        source_list=source_addresses,
                        destination_list=destination_addresses,
                        reverse_source_list=reverse_source_addresses,
                        reverse_destination_list=reverse_destination_addresses,
                        value=member.object.name,
                    )

                case "service":
                    service_name, protocol, is_port_based, port_value = self._add_service_definition(
                        services, member.object
                    )
                    all_protocols.add(protocol)

                    self._append_ports_by_direction_and_protocol(
                        direction=member.direction,
                        protocol=protocol,
                        source_dict=source_ports_by_protocol,
                        destination_dict=destination_ports_by_protocol,
                        reverse_source_dict=reverse_source_ports_by_protocol,
                        reverse_destination_dict=reverse_destination_ports_by_protocol,
                        any_dict=any_ports_by_protocol,
                        value=service_name,
                        append_ports=is_port_based,
                    )

                    self._append_ports_by_direction_and_protocol(
                        direction=member.direction,
                        protocol=protocol,
                        source_dict=source_port_values_by_protocol,
                        destination_dict=destination_port_values_by_protocol,
                        reverse_source_dict=reverse_source_port_values_by_protocol,
                        reverse_destination_dict=reverse_destination_port_values_by_protocol,
                        any_dict=any_port_values_by_protocol,
                        value=port_value,
                        append_ports=is_port_based and port_value is not None,
                    )

                case "servicegroup":
                    service_entries = self._add_service_group_definition(services, member.object)
                    for service_name, protocol, is_port_based, port_value in service_entries:
                        all_protocols.add(protocol)

                        self._append_ports_by_direction_and_protocol(
                            direction=member.direction,
                            protocol=protocol,
                            source_dict=source_ports_by_protocol,
                            destination_dict=destination_ports_by_protocol,
                            reverse_source_dict=reverse_source_ports_by_protocol,
                            reverse_destination_dict=reverse_destination_ports_by_protocol,
                            any_dict=any_ports_by_protocol,
                            value=service_name,
                            append_ports=is_port_based,
                        )

                        self._append_ports_by_direction_and_protocol(
                            direction=member.direction,
                            protocol=protocol,
                            source_dict=source_port_values_by_protocol,
                            destination_dict=destination_port_values_by_protocol,
                            reverse_source_dict=reverse_source_port_values_by_protocol,
                            reverse_destination_dict=reverse_destination_port_values_by_protocol,
                            any_dict=any_port_values_by_protocol,
                            value=port_value,
                            append_ports=is_port_based and port_value is not None,
                        )

                case _:
                    raise ValueError(f"Unsupported rule member type: {member.type}")

        source_addresses = self._dedupe_preserve_order(source_addresses)
        destination_addresses = self._dedupe_preserve_order(destination_addresses)
        reverse_source_addresses = self._dedupe_preserve_order(reverse_source_addresses)
        reverse_destination_addresses = self._dedupe_preserve_order(reverse_destination_addresses)

        for protocol in list(all_protocols):
            source_ports_by_protocol[protocol] = self._dedupe_preserve_order(source_ports_by_protocol.get(protocol, []))
            destination_ports_by_protocol[protocol] = self._dedupe_preserve_order(
                destination_ports_by_protocol.get(protocol, [])
            )
            reverse_source_ports_by_protocol[protocol] = self._dedupe_preserve_order(
                reverse_source_ports_by_protocol.get(protocol, [])
            )
            reverse_destination_ports_by_protocol[protocol] = self._dedupe_preserve_order(
                reverse_destination_ports_by_protocol.get(protocol, [])
            )
            any_ports_by_protocol[protocol] = self._dedupe_preserve_order(any_ports_by_protocol.get(protocol, []))

            source_port_values_by_protocol[protocol] = self._dedupe_preserve_order(
                source_port_values_by_protocol.get(protocol, [])
            )
            destination_port_values_by_protocol[protocol] = self._dedupe_preserve_order(
                destination_port_values_by_protocol.get(protocol, [])
            )
            reverse_source_port_values_by_protocol[protocol] = self._dedupe_preserve_order(
                reverse_source_port_values_by_protocol.get(protocol, [])
            )
            reverse_destination_port_values_by_protocol[protocol] = self._dedupe_preserve_order(
                reverse_destination_port_values_by_protocol.get(protocol, [])
            )
            any_port_values_by_protocol[protocol] = self._dedupe_preserve_order(
                any_port_values_by_protocol.get(protocol, [])
            )

        if self._requires_protocol_split(
            all_protocols=all_protocols,
            source_ports_by_protocol=source_port_values_by_protocol,
            destination_ports_by_protocol=destination_port_values_by_protocol,
            reverse_source_ports_by_protocol=reverse_source_port_values_by_protocol,
            reverse_destination_ports_by_protocol=reverse_destination_port_values_by_protocol,
            any_ports_by_protocol=any_port_values_by_protocol,
        ):
            warnings.append(
                f"PolicyRule '{self.name}' (sequence {self.rule_sequence}) was split into "
                f"multiple terms because it contains multiple protocols with different "
                f"port mappings, which cannot be safely represented as a single term."
            )

            terms = []
            for protocol in sorted(all_protocols):
                term = self._build_base_term(
                    name=self.rendered_term_name(protocol),
                    action=self.action,
                    source_addresses=source_addresses,
                    destination_addresses=destination_addresses,
                    reverse_source_addresses=reverse_source_addresses,
                    reverse_destination_addresses=reverse_destination_addresses,
                )
                term["protocol"] = protocol

                if protocol in self.PORT_BASED_PROTOCOLS:
                    should_include = self._add_port_fields_to_term(
                        term=term,
                        vendor=vendor,
                        source_ports=source_ports_by_protocol.get(protocol, []),
                        destination_ports=destination_ports_by_protocol.get(protocol, []),
                        reverse_source_ports=reverse_source_ports_by_protocol.get(protocol, []),
                        reverse_destination_ports=reverse_destination_ports_by_protocol.get(protocol, []),
                        any_ports=any_ports_by_protocol.get(protocol, []),
                        warnings=warnings,
                    )
                    if not should_include:
                        continue

                terms.append(term)

            return RuleBuildResult(
                terms=terms,
                networks=networks,
                services=services,
                warnings=warnings,
            )

        term = self._build_base_term(
            name=self.rendered_term_name(),
            action=self.action,
            source_addresses=source_addresses,
            destination_addresses=destination_addresses,
            reverse_source_addresses=reverse_source_addresses,
            reverse_destination_addresses=reverse_destination_addresses,
        )

        should_include_term = True

        if all_protocols:
            sorted_protocols = sorted(all_protocols)
            term["protocol"] = sorted_protocols[0] if len(sorted_protocols) == 1 else sorted_protocols

            shared_source_ports = self._dedupe_preserve_order(
                [port for protocol in sorted_protocols for port in source_ports_by_protocol.get(protocol, [])]
            )
            shared_destination_ports = self._dedupe_preserve_order(
                [port for protocol in sorted_protocols for port in destination_ports_by_protocol.get(protocol, [])]
            )
            shared_reverse_source_ports = self._dedupe_preserve_order(
                [port for protocol in sorted_protocols for port in reverse_source_ports_by_protocol.get(protocol, [])]
            )
            shared_reverse_destination_ports = self._dedupe_preserve_order(
                [
                    port
                    for protocol in sorted_protocols
                    for port in reverse_destination_ports_by_protocol.get(protocol, [])
                ]
            )
            shared_any_ports = self._dedupe_preserve_order(
                [port for protocol in sorted_protocols for port in any_ports_by_protocol.get(protocol, [])]
            )

            if any(protocol in self.PORT_BASED_PROTOCOLS for protocol in sorted_protocols):
                should_include_term = self._add_port_fields_to_term(
                    term=term,
                    vendor=vendor,
                    source_ports=shared_source_ports,
                    destination_ports=shared_destination_ports,
                    reverse_source_ports=shared_reverse_source_ports,
                    reverse_destination_ports=shared_reverse_destination_ports,
                    any_ports=shared_any_ports,
                    warnings=warnings,
                )

        return RuleBuildResult(
            terms=[term] if should_include_term else [],
            networks=networks,
            services=services,
            warnings=warnings,
        )

    def _requires_protocol_split(
        self,
        all_protocols: set[str],
        source_ports_by_protocol: dict[str, list[str]],
        destination_ports_by_protocol: dict[str, list[str]],
        reverse_source_ports_by_protocol: dict[str, list[str]],
        reverse_destination_ports_by_protocol: dict[str, list[str]],
        any_ports_by_protocol: dict[str, list[str]],
    ) -> bool:
        """
        Split only when multiple protocols have different port mappings.
        If there are no protocols or only one protocol, no split is needed.
        Non-port-based protocols contribute empty port signatures.
        """
        if len(all_protocols) <= 1:
            return False

        protocols = sorted(all_protocols)
        first_signature = None

        for protocol in protocols:
            signature = (
                tuple(source_ports_by_protocol.get(protocol, [])),
                tuple(destination_ports_by_protocol.get(protocol, [])),
                tuple(reverse_source_ports_by_protocol.get(protocol, [])),
                tuple(reverse_destination_ports_by_protocol.get(protocol, [])),
                tuple(any_ports_by_protocol.get(protocol, [])),
            )

            if first_signature is None:
                first_signature = signature
                continue

            if signature != first_signature:
                return True

        return False

    @staticmethod
    def _build_base_term(
        name: str,
        action: str,
        source_addresses: list[str],
        destination_addresses: list[str],
        reverse_source_addresses: list[str],
        reverse_destination_addresses: list[str],
    ) -> dict:
        term = {
            "name": name,
            "action": action,
        }

        if source_addresses:
            term["source-address"] = source_addresses

        if destination_addresses:
            term["destination-address"] = destination_addresses

        if reverse_source_addresses:
            term["reverse-source-address"] = reverse_source_addresses

        if reverse_destination_addresses:
            term["reverse-destination-address"] = reverse_destination_addresses

        return term

    @staticmethod
    def _append_by_direction(
        direction: str,
        source_list: list[str],
        destination_list: list[str],
        reverse_source_list: list[str],
        reverse_destination_list: list[str],
        value: str,
    ) -> None:
        if direction == "source":
            source_list.append(value)
        elif direction == "destination":
            destination_list.append(value)
        elif direction == "reverse_source":
            reverse_source_list.append(value)
        elif direction == "reverse_destination":
            reverse_destination_list.append(value)
        elif direction == "any":
            source_list.append(value)
            destination_list.append(value)
        else:
            raise ValueError(f"Unsupported rule direction: {direction}")

    @staticmethod
    def _append_ports_by_direction_and_protocol(
        direction: str,
        protocol: str,
        source_dict: dict[str, list[str]],
        destination_dict: dict[str, list[str]],
        reverse_source_dict: dict[str, list[str]],
        reverse_destination_dict: dict[str, list[str]],
        any_dict: dict[str, list[str]],
        value: str | None,
        append_ports: bool,
    ) -> None:
        if not append_ports:
            source_dict.setdefault(protocol, [])
            destination_dict.setdefault(protocol, [])
            reverse_source_dict.setdefault(protocol, [])
            reverse_destination_dict.setdefault(protocol, [])
            any_dict.setdefault(protocol, [])
            return

        if value is None:
            return

        if direction == "source":
            source_dict[protocol].append(value)
        elif direction == "destination":
            destination_dict[protocol].append(value)
        elif direction == "reverse_source":
            reverse_source_dict[protocol].append(value)
        elif direction == "reverse_destination":
            reverse_destination_dict[protocol].append(value)
        elif direction == "any":
            any_dict[protocol].append(value)
        else:
            raise ValueError(f"Unsupported rule direction: {direction}")

    @staticmethod
    def _extend_deduped(target: list[str], values: list[str]) -> list[str]:
        return list(dict.fromkeys([*target, *values]))

    def _add_port_fields_to_term(
        self,
        *,
        term: dict,
        vendor: str,
        source_ports: list[str],
        destination_ports: list[str],
        reverse_source_ports: list[str],
        reverse_destination_ports: list[str],
        any_ports: list[str],
        warnings: list[str],
    ) -> bool:
        if source_ports:
            term["source-port"] = source_ports
        if destination_ports:
            term["destination-port"] = destination_ports
        if reverse_source_ports:
            term["reverse-source-port"] = reverse_source_ports
        if reverse_destination_ports:
            term["reverse-destination-port"] = reverse_destination_ports

        if not any_ports:
            return True

        if vendor_supports(vendor, "supports_neutral_port"):
            term["port"] = any_ports
            return True

        if vendor_supports(vendor, "supports_source_port"):
            existing_source_ports = term.get("source-port", [])
            existing_destination_ports = term.get("destination-port", [])

            term["source-port"] = self._extend_deduped(existing_source_ports, any_ports)
            term["destination-port"] = self._extend_deduped(existing_destination_ports, any_ports)
            return True

        term_name = term.get("name", self.name)
        warnings.append(
            f"PolicyRule '{self.name}' (sequence {self.rule_sequence}) contains service direction 'any', "
            f"but vendor '{vendor}' does not support either neutral 'port' or 'source-port'. "
            f"Skipping term '{term_name}' for this vendor."
        )
        return False

    def _add_address_definition(self, networks: dict[str, dict], address: Address) -> None:
        values = []
        ipv4_addrs, ipv6_addrs = address.get_address()

        for addr in ipv4_addrs:
            values.append(str(addr))

        for addr in ipv6_addrs:
            values.append(str(addr))

        networks[address.name] = {"values": values}

    def _add_address_group_definition(self, networks: dict[str, dict], address_group: AddressGroup) -> None:
        values = []
        for address in get_address_group_members(
            address_group_id=address_group.id,
            actor=self.actor,
            tenant_id=self.tenant_id,
        ):
            ipv4_addrs, ipv6_addrs = address.get_address()

            for addr in ipv4_addrs:
                values.append(str(addr))

            for addr in ipv6_addrs:
                values.append(str(addr))

        networks[address_group.name] = {"values": values}

    def _add_service_definition(
        self,
        services: dict[str, list[dict]],
        service: Service,
    ) -> tuple[str, str, bool, str | None]:
        service_name = service.name
        protocol = service.get_protocol()
        port_value = service.get_ports()
        is_port_based = service.is_port_based()

        entry = {"protocol": protocol}
        if port_value is not None:
            entry["port"] = port_value

        services[service_name] = [entry]
        return service_name, protocol, is_port_based, port_value

    def _add_service_group_definition(
        self,
        services: dict[str, list[dict]],
        service_group: ServiceGroup,
    ) -> list[tuple[str, str, bool, str | None]]:
        service_entries = []

        for service in get_service_group_members(
            service_group_id=service_group.id,
            actor=self.actor,
            tenant_id=self.tenant_id,
        ):
            service_name = service.name
            protocol = service.get_protocol()
            port_value = service.get_ports()
            is_port_based = service.is_port_based()

            entry = {"protocol": protocol}
            if port_value is not None:
                entry["port"] = port_value

            services[service_name] = [entry]
            service_entries.append((service_name, protocol, is_port_based, port_value))

        return service_entries

    @staticmethod
    def _dedupe_preserve_order(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))


class Policy:
    """
    A class for the input to Aerleon's Generate function.

    Each PolicyRule must have:
    - a unique rule_sequence
    - rule_sequence equal to its 1-based position in the filter
    - a rendered term name that is unique within the policy
    """

    def __init__(
        self,
        actor: User,
        tenant_id: int,
        name: str,
        rules: list[PolicyRule],
        vendor: str,
        target_spec: str | list[str] | None = None,
        policy_sequence: int = 0,
    ):
        if rules is None:
            raise ValueError("rules cannot be None")

        self.actor = actor
        self.tenant_id = tenant_id
        self.name = name.strip().replace(" ", "_")
        self.vendor = vendor.lower()
        self.rules = rules
        self.target_spec = target_spec if target_spec not in ("", []) else None
        self.policy_sequence = policy_sequence
        self.build_warnings: list[str] = []

        self._validate_rule_sequences(rules)
        self._validate_rendered_rule_names_unique(rules)
        self._rebuild_policy_contents()

    def _rebuild_policy_contents(self) -> None:
        self.YAMLConfig = self._build_base_yaml()
        self.networks = {"networks": {}}
        self.services = {"services": {}}
        self.build_warnings = []

        used_term_names: set[str] = set()

        for rule in sorted(self.rules, key=lambda r: r.rule_sequence):
            result = rule.build(vendor=self.vendor)

            for warning in result.warnings:
                self.build_warnings.append(warning)
                logger.warning(warning)

            for term in result.terms:
                term_name = term["name"]
                if term_name in used_term_names:
                    raise ValueError(f"Duplicate rendered term name generated in policy '{self.name}': {term_name}")
                used_term_names.add(term_name)

            self._merge_networks(result.networks)
            self._merge_services(result.services)
            self.YAMLConfig["filters"][0]["terms"].extend(result.terms)

    def _build_filter_header(self) -> dict:
        if self.target_spec is None:
            target_value = self.name
        else:
            target_value = self.target_spec

        return {
            "targets": {self.vendor: target_value},
            "comment": f"Generated by Rulio for {self.vendor}",
        }

    def _build_base_yaml(self) -> dict:
        return {
            "filename": self.name,
            "filters": [
                {
                    "header": self._build_filter_header(),
                    "terms": [],
                },
            ],
        }

    @staticmethod
    def _validate_rule_sequences(rules: list[PolicyRule]) -> None:
        sequences = [rule.rule_sequence for rule in rules]

        if len(sequences) != len(set(sequences)):
            raise ValueError("rule_sequence values must be unique")

        expected = list(range(1, len(rules) + 1))
        actual = sorted(sequences)

        if actual != expected:
            raise ValueError(
                f"rule_sequence values must be contiguous and 1-indexed. Expected {expected}, got {actual}"
            )

    @staticmethod
    def _validate_rendered_rule_names_unique(rules: list[PolicyRule]) -> None:
        rendered_names = [rule.rendered_term_name() for rule in rules]
        duplicates = [name for name, count in Counter(rendered_names).items() if count > 1]

        if duplicates:
            raise ValueError(
                "Rendered rule term names must be unique within a policy. "
                f"Duplicate rendered names: {sorted(duplicates)}"
            )

    def _merge_networks(self, networks: dict[str, dict]) -> None:
        for name, value in networks.items():
            if name in self.networks["networks"] and self.networks["networks"][name] != value:
                raise ValueError(f"Duplicate network definition with different values: {name}")
            self.networks["networks"][name] = value

    def _merge_services(self, services: dict[str, list[dict]]) -> None:
        for name, value in services.items():
            if name in self.services["services"] and self.services["services"][name] != value:
                raise ValueError(f"Duplicate service definition with different values: {name}")
            self.services["services"][name] = value

    def set_vendor(self, new_vendor: str, target_spec: str | list[str] | None = None) -> None:
        """
        Update the vendor and target specification used in filter headers.

        Because term rendering is vendor-aware, this rebuilds the policy contents.
        """
        self.vendor = new_vendor.lower()
        self.target_spec = target_spec if target_spec not in ("", []) else None
        self._rebuild_policy_contents()


def _build_warning_diagnostics(policy: Policy) -> list[GenerationDiagnostic]:
    return [
        GenerationDiagnostic(
            source="rulio",
            level="warning",
            code="build_warning",
            message=warning,
        )
        for warning in policy.build_warnings
    ]


def _log_records_to_diagnostics(
    records: list[logging.LogRecord],
) -> tuple[list[GenerationDiagnostic], list[GenerationDiagnostic]]:
    warnings: list[GenerationDiagnostic] = []
    errors: list[GenerationDiagnostic] = []

    for record in records:
        if record.levelno < logging.WARNING:
            continue

        message = record.getMessage().strip()

        if record.levelno >= logging.ERROR:
            errors.append(
                GenerationDiagnostic(
                    source="aerleon",
                    level="error",
                    code="aerleon_error",
                    message=message,
                )
            )
            continue

        match = SHADING_WARNING_PATTERN.match(message)
        if match:
            warnings.append(
                GenerationDiagnostic(
                    source="aerleon",
                    level="warning",
                    code="shading",
                    message=message,
                    term_name=match.group("term").strip(),
                    shaded_by_name=match.group("shaded_by").strip(),
                )
            )
            continue

        warnings.append(
            GenerationDiagnostic(
                source="aerleon",
                level="warning",
                code="aerleon_warning",
                message=message,
            )
        )

    return warnings, errors


def _exception_to_diagnostic(exc: Exception) -> GenerationDiagnostic:
    return GenerationDiagnostic(
        source="aerleon",
        level="error",
        code="aerleon_error",
        message=str(exc).strip() or exc.__class__.__name__,
    )


def _dedupe_diagnostics(diagnostics: list[GenerationDiagnostic]) -> list[GenerationDiagnostic]:
    seen: set[tuple[str, str, str, str, str | None, str | None]] = set()
    deduped: list[GenerationDiagnostic] = []

    for diagnostic in diagnostics:
        key = (
            diagnostic.source,
            diagnostic.level,
            diagnostic.code,
            diagnostic.message,
            diagnostic.term_name,
            diagnostic.shaded_by_name,
        )
        if key in seen:
            continue

        seen.add(key)
        deduped.append(diagnostic)

    return deduped


def _generate_from_policy(policy: Policy) -> ConfigGenerationResult:
    warnings = _build_warning_diagnostics(policy)
    errors: list[GenerationDiagnostic] = []

    definitions = naming.Naming()
    definitions_obj = {
        "networks": policy.networks.get("networks", {}),
        "services": policy.services.get("services", {}),
    }

    capture_handler = _AerleonLogCaptureHandler()
    capture_handler.setLevel(logging.WARNING)

    root_logger = logging.getLogger()
    root_logger.addHandler(capture_handler)

    try:
        definitions.ParseDefinitionsObject(definitions_obj, policy.name)
        config = aerleon_api.Generate([policy.YAMLConfig], definitions, shade_check=True)
    except Exception as exc:
        logged_warnings, logged_errors = _log_records_to_diagnostics(capture_handler.records)
        warnings.extend(logged_warnings)
        errors.extend(logged_errors)
        errors.append(_exception_to_diagnostic(exc))

        warnings = _dedupe_diagnostics(warnings)
        errors = _dedupe_diagnostics(errors)

        return ConfigGenerationResult(
            config=None,
            warnings=warnings,
            errors=errors,
        )
    finally:
        root_logger.removeHandler(capture_handler)

    logged_warnings, logged_errors = _log_records_to_diagnostics(capture_handler.records)
    warnings.extend(logged_warnings)
    errors.extend(logged_errors)

    warnings = _dedupe_diagnostics(warnings)
    errors = _dedupe_diagnostics(errors)

    return ConfigGenerationResult(
        config=config,
        warnings=warnings,
        errors=errors,
    )


def merge_policies(policies: list[Policy], name: str | None = None) -> Policy:
    if not policies:
        raise ValueError("No policies provided for merging.")

    policies = sorted(policies, key=lambda p: p.policy_sequence)
    merged_policy = copy.deepcopy(policies[0])

    for policy in policies[1:]:
        for network_name, value in policy.networks.get("networks", {}).items():
            if (
                network_name in merged_policy.networks.get("networks", {})
                and merged_policy.networks["networks"][network_name] != value
            ):
                raise ValueError(f"Duplicate network definition with different values: {network_name}")
            merged_policy.networks["networks"][network_name] = value

        for service_name, value in policy.services.get("services", {}).items():
            if (
                service_name in merged_policy.services.get("services", {})
                and merged_policy.services["services"][service_name] != value
            ):
                raise ValueError(f"Duplicate service definition with different values: {service_name}")
            merged_policy.services["services"][service_name] = value

        filter_config = copy.deepcopy(policy.YAMLConfig["filters"][0])
        merged_policy.YAMLConfig["filters"].append(filter_config)
        merged_policy.build_warnings.extend(policy.build_warnings)

    if name:
        normalized_name = name.strip().replace(" ", "_")
        merged_policy.name = normalized_name
        merged_policy.YAMLConfig["filename"] = normalized_name

    for filter_config in merged_policy.YAMLConfig["filters"]:
        if merged_policy.target_spec is None:
            filter_config["header"] = merged_policy._build_filter_header()

    return merged_policy


def generate_config(policy: Policy) -> ConfigGenerationResult:
    """
    Generates a configuration for the specified vendor based on the provided policy.

    Args:
        policy (Policy): The policy object containing the assembled Aerleon YAML
            configuration and object definitions.

    Returns:
        ConfigGenerationResult: Generated configuration and any collected warnings/errors.
    """
    return _generate_from_policy(policy)


def generate_multi_policy_config(policies: list[Policy], name: str | None = None) -> ConfigGenerationResult:
    """
    Generates a configuration for the specified vendor based on the provided list of Policy objects.

    Args:
        policies (list[Policy]): A list of Policy objects to merge and convert into configuration.
        name (str | None): Optional name to assign to the merged policy.

    Returns:
        ConfigGenerationResult: Generated configuration and any collected warnings/errors.
    """
    merged_policy = merge_policies(policies, name)
    return _generate_from_policy(merged_policy)