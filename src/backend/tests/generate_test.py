import copy
import logging
import string

import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.service import Service
from backend.services.attribute_objects.create_attribute_objects import get_or_create_address
from backend.services.config_generation.generate_config import (
    GenerationDiagnostic,
    Policy,
    PolicyRule,
    PolicyRuleMember,
    _dedupe_diagnostics,
    _exception_to_diagnostic,
    _log_records_to_diagnostics,
    generate_config,
    generate_multi_policy_config,
    merge_policies,
)
from backend.services.config_generation.icmp import get_aerleon_icmp_code, get_aerleon_icmp_type
from backend.services.config_generation.platform_capabilities import (
    PLATFORM_CAPABILITIES,
    PlatformCapabilities,
    get_platform_capabilities,
    resolve_platform_direction,
    vendor_supports,
)
from backend.utils.logger import clear_logs, set_up_logger
from backend.utils.write_to_file import write_configuration_to_file
from constants import TEST_LOGPATH

logger = set_up_logger(__name__)
clear_logs(__name__)


@pytest.mark.django_db
class TestGenerateConfig:
    vendor_target_options_pairs = [
        ("juniper", None),
        ("arista", None),
        ("aruba", None),
        ("cisco", None),
        ("brocade", None),
        ("paloalto", ["from-zone", "internal", "to-zone", "external"]),
    ]
    log_for_vendors = ["juniper"]

    def _extract_generated_text(self, config) -> str:
        assert config
        assert hasattr(config, "keys")
        assert len(config.keys()) >= 1

        generated_texts = list(config.values())
        assert all(isinstance(text, str) for text in generated_texts)
        generated_text = "\n".join(generated_texts)
        assert generated_text
        assert len(generated_text.strip()) > 0

        return generated_text

    def _generate_for_all_vendors(self, policy, output_subdir: str, output_prefix: str):
        generated_outputs = {}
        generation_failures = []

        for vendor, target_options in self.vendor_target_options_pairs:
            vendor_policy = copy.deepcopy(policy)
            vendor_policy.set_vendor(vendor, target_options)

            result = generate_config(vendor_policy)
            if not result.success:
                generation_failures.append(
                    f"{vendor}: {[error.message for error in result.errors]}"
                )
                generated_outputs[vendor] = {"text": "", "result": result}
                continue

            generated_text = self._extract_generated_text(result.config)

            filepath = TEST_LOGPATH / output_subdir / f"{vendor.upper()}_{output_prefix}_generated_config.txt"
            filedir = TEST_LOGPATH / output_subdir
            write_configuration_to_file(
                result.config,
                filepath,
                filedir,
                vendor,
                __name__,
                generated_by=vendor,
                log_for_vendors=self.log_for_vendors,
            )

            generated_outputs[vendor] = {
                "text": generated_text,
                "result": result,
            }

        if generation_failures:
            pytest.fail("Generation failed for vendors:\n" + "\n".join(generation_failures))

        return generated_outputs

    @staticmethod
    def _assert_config_has_common_service_content(config_text: str) -> None:
        assert "80" in config_text or "www" in config_text
        assert "53" in config_text or "domain" in config_text

    @staticmethod
    def _assert_config_exists_only(config_text: str) -> None:
        assert config_text
        assert isinstance(config_text, str)
        assert len(config_text.strip()) > 0

    @staticmethod
    def _vendor_supports_any_service_render(vendor: str) -> bool:
        capabilities = get_platform_capabilities(vendor)
        return capabilities.supports_neutral_port or capabilities.supports_source_port

    def test_generate_address_config(self, built_address_policy):
        configs = self._generate_for_all_vendors(
            policy=built_address_policy,
            output_subdir="addr",
            output_prefix="address",
        )
        vendor_assertion_failures = []

        for vendor, output in configs.items():
            config = output["text"]
            capabilities = get_platform_capabilities(vendor)

            if capabilities.supports_ipv6 and "ff00::/120" not in config:
                vendor_assertion_failures.append(f"{vendor}: output omitted IPv6 address ff00::/120")

            if vendor == "paloalto":
                if not config:
                    vendor_assertion_failures.append(f"{vendor}: output is empty")
                continue

            if "192.168.1.0" not in config:
                vendor_assertion_failures.append(f"{vendor}: output omitted IPv4 address 192.168.1.0")

        juniper_config = configs["juniper"]["text"]
        for expected in ("Test_Address_Rule_1", "Test_Address_Rule_2", "192.168.1.0/24"):
            if expected not in juniper_config:
                vendor_assertion_failures.append(f"juniper: output omitted {expected}")

        if vendor_assertion_failures:
            pytest.fail("Generated output checks failed:\n" + "\n".join(vendor_assertion_failures))

    def test_generate_ipv6_addresses_and_address_groups(self, built_address_policy, built_address_group_policy):
        for policy in (built_address_policy, built_address_group_policy):
            policy.set_vendor("juniper")
            network_values = [
                value
                for definition in policy.networks["networks"].values()
                for value in definition["values"]
            ]

            assert "ff00::/120" in network_values

            result = generate_config(policy)

            assert result.success, [error.message for error in result.errors]
            generated_text = "\n".join(result.config.values())
            assert "family inet " in generated_text
            assert "family inet6 " in generated_text
            assert "ff00::/120" in generated_text

    @pytest.mark.parametrize("vendor", ["juniper", "aruba"])
    def test_generate_ipv6_only_address_config(self, sample_addresses, vendor):
        policy = _policy(
            [
                _rule(
                    "IPv6_Only_Rule",
                    [PolicyRuleMember("address", "destination", sample_addresses[2])],
                )
            ],
            name="IPv6_Only_Policy",
        )
        policy.set_vendor(vendor)

        result = generate_config(policy)

        assert result.success, [error.message for error in result.errors]
        generated_text = "\n".join(result.config.values())
        if vendor == "juniper":
            assert "family inet6 " in generated_text
        assert "ff00::/120" in generated_text

    def test_generate_ipv6_fails_for_unsupported_vendor(self, sample_addresses):
        policy = _policy(
            [
                _rule(
                    "IPv6_Only_Rule",
                    [PolicyRuleMember("address", "destination", sample_addresses[2])],
                )
            ],
            vendor="ciscoasa",
            name="IPv6_Only_Policy",
        )

        result = generate_config(policy)

        assert not result.success
        assert result.config is None
        assert any(error.code == "unsupported_ipv6" for error in result.errors)

    def test_dual_stack_split_keeps_protocol_split_terms(self):
        dual_stack_address = Address(
            name="Dual_Stack_Network",
            tenant_id=1,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="192.0.2.0/24",
            ipv6_type="standard",
            ipv6Network="2001:db8:1::/48",
        )
        rule = _rule(
            "Dual_Stack_Split",
            [
                PolicyRuleMember("address", "source", dual_stack_address),
                PolicyRuleMember("service", "destination", _service("WEB", "tcp", 80)),
                PolicyRuleMember("service", "destination", _service("DNS", "udp", 53)),
            ],
        )

        result = generate_config(_policy([rule]))

        assert result.success, [error.message for error in result.errors]
        generated_text = "\n".join(result.config.values())
        assert "family inet " in generated_text
        assert "family inet6 " in generated_text
        assert "192.0.2.0/24" in generated_text
        assert "2001:db8:1::/48" in generated_text
        assert "Dual_Stack_Split-tcp" in generated_text
        assert "Dual_Stack_Split-udp" in generated_text

    def test_build_address_with_spaces_uses_normalized_network_name(self, request_with_session, create_testing_tenant):
        address = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Browser ACL Address",
            description="Frontend-created address",
            ipv4_auto="198.51.100.0/24",
        )[0]

        result = PolicyRule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Browser ACL Rule",
            action="accept",
            rule_sequence=1,
            members=[PolicyRuleMember("address", "source", address)],
        ).build(vendor="juniper")

        assert "Browser_ACL_Address" in result.networks
        assert result.terms[0]["source-address"] == ["Browser_ACL_Address"]

    def test_generate_address_group_config(self, built_address_group_policy):
        configs = self._generate_for_all_vendors(
            policy=built_address_group_policy,
            output_subdir="addr_group",
            output_prefix="address_group",
        )

        for vendor, output in configs.items():
            config = output["text"]

            if vendor == "paloalto":
                assert config
                continue

            assert "10.0.0.0" in config
            assert "172.16.0.0" in config

        juniper_config = configs["juniper"]["text"]
        assert "Test_Rule_for_Address_Group_1" in juniper_config
        assert "Test_Rule_for_Address_Group_2" in juniper_config
        assert "10.0.0.0/8" in juniper_config

    def test_generate_service_config(self, built_service_policy):
        configs = self._generate_for_all_vendors(
            policy=built_service_policy,
            output_subdir="service",
            output_prefix="service",
        )

        for vendor, output in configs.items():
            config = output["text"]

            if vendor == "paloalto":
                assert config
                continue

            self._assert_config_has_common_service_content(config)

        juniper_config = configs["juniper"]["text"]
        assert "Test_Service_Rule_1" in juniper_config
        assert "Test_Service_Rule_2" in juniper_config
        assert "destination-port 80;" in juniper_config
        assert "protocol tcp;" in juniper_config

    def test_generate_icmp_service_config(self, built_icmp_policy):
        for vendor, target_options in self.vendor_target_options_pairs:
            vendor_policy = copy.deepcopy(built_icmp_policy)
            vendor_policy.set_vendor(vendor, target_options)

            result = generate_config(vendor_policy)
            capabilities = get_platform_capabilities(vendor)

            if capabilities.supports_icmp_type and capabilities.supports_icmp_code:
                assert result.success, [error.message for error in result.errors]

                generated_text = self._extract_generated_text(result.config)

                filepath = TEST_LOGPATH / "icmp" / f"{vendor.upper()}_icmp_generated_config.txt"
                filedir = TEST_LOGPATH / "icmp"
                write_configuration_to_file(
                    result.config,
                    filepath,
                    filedir,
                    vendor,
                    __name__,
                    generated_by=vendor,
                    log_for_vendors=self.log_for_vendors,
                )

                if vendor == "juniper":
                    assert "Allow_ICMP_Unreachable" in generated_text
                    assert "protocol icmp;" in generated_text
                    assert "icmp-type 3;" in generated_text
                    assert "icmp-code 3;" in generated_text

            elif capabilities.supports_icmp_type and not capabilities.supports_icmp_code:
                assert not result.success
                assert any("does not support ICMP code matching" in warning.message for warning in result.warnings)
                assert any("no terms found" in error.message.lower() for error in result.errors)

            else:
                assert not result.success
                assert any(
                    "does not support ICMP type matching" in warning.message
                    or "does not support ICMP code matching" in warning.message
                    for warning in result.warnings
                )
                assert any("no terms found" in error.message.lower() for error in result.errors)

    def test_generate_service_group_config(self, built_service_group_policy):
        configs = self._generate_for_all_vendors(
            policy=built_service_group_policy,
            output_subdir="service_group",
            output_prefix="service_group",
        )

        for vendor, output in configs.items():
            config = output["text"]
            result = output["result"]

            if self._vendor_supports_any_service_render(vendor):
                self._assert_config_has_common_service_content(config)
                continue

            self._assert_config_exists_only(config)
            assert any("contains service direction 'any'" in warning.message for warning in result.warnings)

        juniper_config = configs["juniper"]["text"]
        assert "Test_Rule_for_Service_Group_1" in juniper_config
        assert "protocol tcp;" in juniper_config
        assert "protocol udp;" in juniper_config
        assert "port [ 53 80 1000-2000 ];" in juniper_config
        assert "port [ 53 3000-4000 ];" in juniper_config

    def test_generate_combined_config(self, built_combined_policy):
        configs = self._generate_for_all_vendors(
            policy=built_combined_policy,
            output_subdir="combined",
            output_prefix="combined",
        )

        for vendor, output in configs.items():
            config = output["text"]

            if vendor == "paloalto":
                assert config
                continue

            assert "192.168.1.0" in config
            assert "80" in config or "www" in config
            assert "53" in config or "domain" in config

        juniper_config = configs["juniper"]["text"]
        assert "Combined_Rule_1" in juniper_config
        assert "Combined_Rule_2" in juniper_config
        assert "destination-port 80;" in juniper_config

    def test_generate_realistic_router_policy(self, built_realistic_acl_policy):
        configs = self._generate_for_all_vendors(
            policy=built_realistic_acl_policy,
            output_subdir="realistic",
            output_prefix="realistic",
        )

        for vendor, output in configs.items():
            config = output["text"]

            if vendor == "paloalto":
                assert config
                continue

            assert "10.20.20.0" in config
            assert "172.16.20.53" in config
            assert "443" in config or "https" in config

        juniper_config = configs["juniper"]["text"]
        assert "Allow_Trusted_To_Web" in juniper_config
        assert "Allow_Trusted_To_DNS" in juniper_config
        assert "Deny_Admins_To_Blocked" in juniper_config
        assert "Allow_Admins_ICMP" in juniper_config
        assert "protocol icmp;" in juniper_config

    def test_generate_multi_policy_config(self, built_interface_policies):
        for vendor, target_options in self.vendor_target_options_pairs:
            vendor_policies = copy.deepcopy(built_interface_policies)

            for policy in vendor_policies:
                policy.set_vendor(vendor, target_options)

            result = generate_multi_policy_config(vendor_policies)
            assert result.success, [error.message for error in result.errors]

            generated_text = self._extract_generated_text(result.config)

            filepath = TEST_LOGPATH / "multi" / f"{vendor.upper()}_multi_generated_config.txt"
            filedir = TEST_LOGPATH / "multi"
            write_configuration_to_file(
                result.config,
                filepath,
                filedir,
                vendor,
                __name__,
                generated_by=vendor,
                log_for_vendors=self.log_for_vendors,
            )

            assert generated_text

    def test_merge_policies_preserves_multiple_filters(self, built_interface_policies):
        merged_policy = merge_policies(copy.deepcopy(built_interface_policies))

        assert merged_policy is not None
        assert len(merged_policy.YAMLConfig["filters"]) == len(built_interface_policies)

        result = generate_config(merged_policy)
        assert result.success, [error.message for error in result.errors]

        generated_text = self._extract_generated_text(result.config)

        write_configuration_to_file(
            result.config,
            TEST_LOGPATH / "merged" / "MERGED_generated_config.txt",
            TEST_LOGPATH / "merged",
            merged_policy.vendor,
            __name__,
            generated_by="merged",
            log_for_vendors=self.log_for_vendors,
        )

        assert generated_text

    def test_shading_check(self, built_shading_policy):
        result = generate_config(built_shading_policy)
        logger.info(f"Shading check result: {[warning.message for warning in result.warnings]}")
        assert result.success, [error.message for error in result.errors]

        shading_warnings = [warning for warning in result.warnings if warning.code == "shading"]

        assert shading_warnings, f"Expected shading warning, got: {result.warnings}"
        assert any("is shaded by" in warning.message for warning in shading_warnings)
        assert any(warning.term_name is not None and warning.shaded_by_name is not None for warning in shading_warnings)


def _address(name: str, network: str) -> Address:
    return Address(name=name, tenant_id=1, addr_type="network", ipv4_type="standard", ipv4Network=network)


def _service(
    name: str,
    protocol: str,
    port: int | None = None,
    icmp_type: int | None = None,
    icmp_code: int | None = None,
) -> Service:
    return Service(
        name=name,
        tenant_id=1,
        protocol=protocol,
        port_start=port,
        port_end=port,
        icmp_type=icmp_type,
        icmp_code=icmp_code,
    )


def _rule(name: str, members: list[PolicyRuleMember], rule_sequence: int = 1, action: str = "accept") -> PolicyRule:
    return PolicyRule(
        actor=None,
        tenant_id=1,
        name=name,
        action=action,
        rule_sequence=rule_sequence,
        members=members,
    )


def _policy(rules: list[PolicyRule], vendor: str = "juniper", name: str = "Unit_Policy", **kwargs) -> Policy:
    return Policy(actor=None, tenant_id=1, name=name, rules=rules, vendor=vendor, **kwargs)


def _source_address_rule(name: str, rule_sequence: int = 1, network: str = "10.0.0.0/8") -> PolicyRule:
    return _rule(name, [PolicyRuleMember("address", "source", _address("Net", network))], rule_sequence)


def _split_rule(name: str, rule_sequence: int = 1) -> PolicyRule:
    return _rule(
        name,
        [
            PolicyRuleMember("service", "destination", _service("WEB", "tcp", 80)),
            PolicyRuleMember("service", "destination", _service("DNS", "udp", 53)),
        ],
        rule_sequence,
    )


class TestPolicyRuleMember:
    def test_normalizes_type_and_direction(self):
        member = PolicyRuleMember(" Address ", " SOURCE ", _address("Net", "10.0.0.0/8"))

        assert member.type == "address"
        assert member.direction == "source"

    def test_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid obj_type"):
            PolicyRuleMember("network", "source", _address("Net", "10.0.0.0/8"))

    def test_rejects_invalid_direction(self):
        with pytest.raises(ValueError, match="Invalid direction"):
            PolicyRuleMember("address", "inbound", _address("Net", "10.0.0.0/8"))

    def test_rejects_object_of_wrong_class(self):
        with pytest.raises(TypeError, match="must be of type Address, got Service"):
            PolicyRuleMember("address", "source", _service("WEB", "tcp", 80))


class TestPolicyRuleBuild:
    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"name": "   "}, "name cannot be empty"),
            ({"action": ""}, "action cannot be empty"),
            ({"rule_sequence": 0}, "rule_sequence must be >= 1"),
            ({"members": None}, "members cannot be None"),
            ({"members": []}, "at least one member"),
        ],
    )
    def test_rejects_invalid_input(self, overrides, message):
        kwargs = {
            "actor": None,
            "tenant_id": 1,
            "name": "Valid_Rule",
            "action": "accept",
            "rule_sequence": 1,
            "members": [PolicyRuleMember("address", "source", _address("Net", "10.0.0.0/8"))],
        }
        kwargs.update(overrides)

        with pytest.raises(ValueError, match=message):
            PolicyRule(**kwargs)

    def test_normalizes_name_and_action(self):
        rule = _rule(
            " Allow web ",
            [PolicyRuleMember("address", "source", _address("Net", "10.0.0.0/8"))],
            action=" ACCEPT ",
        )

        assert rule.name == "Allow_web"
        assert rule.action == "accept"

    def test_rendered_term_name_is_truncated_and_keeps_suffix(self):
        rule = _source_address_rule("X" * 80)

        assert rule.rendered_term_name() == "X" * 62
        assert rule.rendered_term_name("tcp") == "X" * 58 + "-tcp"

    @pytest.mark.parametrize(
        ("direction", "expected_keys"),
        [
            ("source", ["source-address"]),
            ("destination", ["destination-address"]),
            ("reverse_source", ["reverse-source-address"]),
            ("reverse_destination", ["reverse-destination-address"]),
            ("any", ["source-address", "destination-address"]),
        ],
    )
    def test_address_direction_maps_to_term_fields(self, direction, expected_keys):
        result = _rule("Dir", [PolicyRuleMember("address", direction, _address("My Net", "10.0.0.0/8"))]).build(
            "juniper"
        )

        term = result.terms[0]
        address_keys = sorted(key for key in term if key.endswith("-address"))
        assert address_keys == sorted(expected_keys)
        for key in expected_keys:
            assert term[key] == ["My_Net"]
        assert result.networks == {"My_Net": {"values": ["10.0.0.0/8"]}}

    def test_duplicate_members_are_deduplicated(self):
        address = _address("Net", "10.0.0.0/8")
        result = _rule(
            "Dupes",
            [PolicyRuleMember("address", "source", address), PolicyRuleMember("address", "source", address)],
        ).build("juniper")

        assert result.terms[0]["source-address"] == ["Net"]

    @pytest.mark.parametrize(
        ("vendor", "expected_fields"),
        [
            ("juniper", {"port": ["WEB"]}),
            ("cisco", {"source-port": ["WEB"], "destination-port": ["WEB"]}),
        ],
    )
    def test_any_service_direction_per_vendor(self, vendor, expected_fields):
        result = _rule("Any_Svc", [PolicyRuleMember("service", "any", _service("WEB", "tcp", 80))]).build(vendor)

        assert result.warnings == []
        term = result.terms[0]
        port_fields = {key: term[key] for key in ("port", "source-port", "destination-port") if key in term}
        assert port_fields == expected_fields

    def test_any_service_direction_skipped_for_unsupported_vendor(self):
        result = _rule("Any_Svc", [PolicyRuleMember("service", "any", _service("WEB", "tcp", 80))]).build("aruba")

        assert result.terms == []
        assert any("contains service direction 'any'" in warning for warning in result.warnings)

    def test_protocols_with_different_ports_are_split(self):
        result = _split_rule("Split").build("juniper")

        assert [term["name"] for term in result.terms] == ["Split-tcp", "Split-udp"]
        assert result.terms[0]["protocol"] == "tcp"
        assert result.terms[0]["destination-port"] == ["WEB"]
        assert result.terms[1]["protocol"] == "udp"
        assert result.terms[1]["destination-port"] == ["DNS"]
        assert any("was split into multiple terms" in warning for warning in result.warnings)

    def test_protocols_with_same_ports_share_one_term(self):
        result = _rule(
            "Shared",
            [
                PolicyRuleMember("service", "destination", _service("DNS_TCP", "tcp", 53)),
                PolicyRuleMember("service", "destination", _service("DNS_UDP", "udp", 53)),
            ],
        ).build("juniper")

        assert result.warnings == []
        assert len(result.terms) == 1
        assert result.terms[0]["protocol"] == ["tcp", "udp"]
        assert result.terms[0]["destination-port"] == ["DNS_TCP", "DNS_UDP"]

    def test_icmpv6_type_is_mapped(self):
        result = _rule(
            "Ping6", [PolicyRuleMember("service", "destination", _service("Echo6", "icmpv6", icmp_type=128))]
        ).build("juniper")

        assert result.warnings == []
        assert result.terms[0]["protocol"] == "icmpv6"
        assert result.terms[0]["icmp-type"] == ["echo-request"]

    def test_icmp_without_type_or_code_matches_protocol_only(self):
        result = _rule("Any_ICMP", [PolicyRuleMember("service", "destination", _service("ICMP", "icmp"))]).build(
            "juniper"
        )

        assert result.warnings == []
        assert result.terms == [{"name": "Any_ICMP", "action": "accept", "protocol": "icmp"}]

    @pytest.mark.parametrize(
        ("service", "message"),
        [
            (_service("Code_Only", "icmp", icmp_code=3), "contains ICMP code without ICMP type"),
            (_service("Bad_Type", "icmp", icmp_type=99), "has unsupported ICMP type '99'"),
        ],
    )
    def test_invalid_icmp_service_is_skipped(self, service, message):
        result = _rule("Bad_ICMP", [PolicyRuleMember("service", "destination", service)]).build("juniper")

        assert result.terms == []
        assert any(message in warning for warning in result.warnings)

    def test_multiple_icmp_types_in_one_term_are_skipped(self):
        result = _rule(
            "Multi_ICMP",
            [
                PolicyRuleMember("service", "destination", _service("Echo", "icmp", icmp_type=8)),
                PolicyRuleMember("service", "destination", _service("Reply", "icmp", icmp_type=0)),
            ],
        ).build("juniper")

        assert result.terms == []
        assert any("multiple ICMP type/code matches" in warning for warning in result.warnings)

    def test_icmp_and_icmpv6_are_split(self):
        result = _rule(
            "Mixed_ICMP",
            [
                PolicyRuleMember("service", "destination", _service("Echo", "icmp", icmp_type=8)),
                PolicyRuleMember("service", "destination", _service("Echo6", "icmpv6", icmp_type=128)),
            ],
        ).build("juniper")

        assert [(term["name"], term["protocol"]) for term in result.terms] == [
            ("Mixed_ICMP-icmp", "icmp"),
            ("Mixed_ICMP-icmpv6", "icmpv6"),
        ]
        assert all(term["icmp-type"] == ["echo-request"] for term in result.terms)


class TestPolicy:
    def test_rejects_duplicate_rule_sequences(self):
        with pytest.raises(ValueError, match="rule_sequence values must be unique"):
            _policy([_source_address_rule("A", 1), _source_address_rule("B", 1)])

    def test_rejects_non_contiguous_rule_sequences(self):
        with pytest.raises(ValueError, match="contiguous and 1-indexed"):
            _policy([_source_address_rule("A", 1), _source_address_rule("B", 3)])

    def test_rejects_names_that_collide_after_truncation(self):
        with pytest.raises(ValueError, match="Rendered rule term names must be unique"):
            _policy([_source_address_rule("A" * 70, 1), _source_address_rule("A" * 70 + "B", 2)])

    def test_rejects_conflicting_network_definitions(self):
        with pytest.raises(ValueError, match="Duplicate network definition with different values: Net"):
            _policy([_source_address_rule("A", 1, "10.0.0.0/8"), _source_address_rule("B", 2, "172.16.0.0/12")])

    def test_rejects_conflicting_service_definitions(self):
        rules = [
            _rule("A", [PolicyRuleMember("service", "destination", _service("WEB", "tcp", 80))], 1),
            _rule("B", [PolicyRuleMember("service", "destination", _service("WEB", "tcp", 8080))], 2),
        ]

        with pytest.raises(ValueError, match="Duplicate service definition with different values: WEB"):
            _policy(rules)

    def test_shared_objects_across_rules_are_allowed(self):
        policy = _policy([_source_address_rule("A", 1), _source_address_rule("B", 2)])

        assert policy.networks == {"networks": {"Net": {"values": ["10.0.0.0/8"]}}}
        assert [term["name"] for term in policy.YAMLConfig["filters"][0]["terms"]] == ["A", "B"]

    def test_terms_are_ordered_by_rule_sequence(self):
        policy = _policy([_source_address_rule("Second", 2), _source_address_rule("First", 1)])

        assert [term["name"] for term in policy.YAMLConfig["filters"][0]["terms"]] == ["First", "Second"]

    @pytest.mark.parametrize(
        ("target_options", "expected_target"),
        [(None, "My_Policy"), ([], "My_Policy"), (["noverbose"], "My_Policy noverbose")],
    )
    def test_filter_header_target(self, target_options, expected_target):
        policy = _policy(
            [_source_address_rule("A")], vendor="Cisco", name="My Policy", target_options=target_options
        )

        assert policy.name == "My_Policy"
        assert policy.YAMLConfig["filename"] == "My_Policy"
        assert policy.YAMLConfig["filters"][0]["header"]["targets"] == {"cisco": expected_target}

    def test_set_vendor_rebuilds_terms(self):
        policy = _policy([_rule("Any_Svc", [PolicyRuleMember("service", "any", _service("WEB", "tcp", 80))])])
        assert policy.YAMLConfig["filters"][0]["terms"][0]["port"] == ["WEB"]

        policy.set_vendor("cisco")

        term = policy.YAMLConfig["filters"][0]["terms"][0]
        assert "port" not in term
        assert term["source-port"] == ["WEB"]
        assert policy.YAMLConfig["filters"][0]["header"]["targets"] == {"cisco": "Unit_Policy mixed"}

    def test_split_warnings_are_aggregated(self):
        policy = _policy([_split_rule("Split_A", 1), _source_address_rule("Plain", 2), _split_rule("Split_B", 3)])

        assert [warning.code for warning in policy.build_warnings] == ["rule_split"]
        assert "sequences 1 and 3" in policy.build_warnings[0].message

    @pytest.mark.parametrize(
        ("sequences", "expected"),
        [
            ([4], "sequence 4 "),
            ([3, 1, 3], "sequences 1 and 3 "),
            ([5, 1, 2], "sequences 1, 2, and 5 "),
        ],
    )
    def test_aggregated_split_warning_formatting(self, sequences, expected):
        warning = Policy._build_aggregated_rule_split_warning(sequences)

        assert warning.code == "rule_split"
        assert warning.message.startswith(expected)

    def test_skipped_terms_are_reported_as_build_warnings(self):
        policy = _policy(
            [_rule("Bad", [PolicyRuleMember("service", "destination", _service("C", "icmp", icmp_code=3))])]
        )

        assert [warning.code for warning in policy.build_warnings] == ["build_warning"]
        assert policy.YAMLConfig["filters"][0]["terms"] == []


class TestGenerateConfigOutput:
    def test_accept_and_deny_actions_render_for_juniper(self):
        policy = _policy(
            [
                _rule("Allow_It", [PolicyRuleMember("address", "source", _address("Allowed", "10.0.0.0/8"))], 1),
                _rule(
                    "Deny_It",
                    [PolicyRuleMember("address", "source", _address("Denied", "172.16.0.0/12"))],
                    2,
                    action="deny",
                ),
            ]
        )

        result = generate_config(policy)

        assert result.success, [error.message for error in result.errors]
        config = next(iter(result.config.values()))
        allow_term, deny_term = config.split("term Allow_It")[1].split("term Deny_It")
        assert "then accept;" in allow_term
        assert "discard;" in deny_term
        assert "10.0.0.0/8" in allow_term
        assert "172.16.0.0/12" in deny_term

    def test_split_rule_renders_one_term_per_protocol(self):
        result = generate_config(_policy([_split_rule("Split")]))

        assert result.success, [error.message for error in result.errors]
        config = next(iter(result.config.values()))
        tcp_term, udp_term = config.split("term Split-tcp")[1].split("term Split-udp")
        assert "protocol tcp;" in tcp_term
        assert "destination-port 80;" in tcp_term
        assert "protocol udp;" in udp_term
        assert "destination-port 53;" in udp_term
        assert [warning.code for warning in result.warnings] == ["rule_split"]

    def test_policy_without_terms_returns_error_instead_of_raising(self):
        policy = _policy(
            [_rule("Bad", [PolicyRuleMember("service", "destination", _service("C", "icmp", icmp_code=3))])]
        )

        result = generate_config(policy)

        assert result.config is None
        assert not result.success
        assert any(error.code == "aerleon_error" and "no terms found" in error.message for error in result.errors)
        assert [warning.code for warning in result.warnings if warning.source == "rulio"] == ["build_warning"]


class TestMergePolicies:
    def test_rejects_empty_list(self):
        with pytest.raises(ValueError, match="No policies provided"):
            merge_policies([])

    def test_orders_filters_by_policy_sequence(self):
        first = _policy([_source_address_rule("From_First")], name="First", policy_sequence=1)
        second = _policy([_source_address_rule("From_Second")], name="Second", policy_sequence=2)

        merged = merge_policies([second, first])

        assert [f["terms"][0]["name"] for f in merged.YAMLConfig["filters"]] == ["From_First", "From_Second"]

    def test_renames_merged_policy(self):
        merged = merge_policies([_policy([_source_address_rule("A")])], name="Merged Policy")

        assert merged.name == "Merged_Policy"
        assert merged.YAMLConfig["filename"] == "Merged_Policy"

    def test_does_not_mutate_input_policies(self):
        first = _policy([_source_address_rule("A")], name="First", policy_sequence=1)
        second = _policy([_split_rule("B")], name="Second", policy_sequence=2)

        merged = merge_policies([first, second])

        assert len(merged.YAMLConfig["filters"]) == 2
        assert len(first.YAMLConfig["filters"]) == 1
        assert first.build_warnings == []
        assert [warning.code for warning in merged.build_warnings] == ["rule_split"]

    def test_rejects_conflicting_networks_across_policies(self):
        first = _policy([_source_address_rule("A", network="10.0.0.0/8")], name="First", policy_sequence=1)
        second = _policy([_source_address_rule("B", network="172.16.0.0/12")], name="Second", policy_sequence=2)

        with pytest.raises(ValueError, match="Duplicate network definition with different values: Net"):
            merge_policies([first, second])

    def test_rejects_conflicting_services_across_policies(self):
        first = _policy(
            [_rule("A", [PolicyRuleMember("service", "destination", _service("WEB", "tcp", 80))])],
            name="First",
            policy_sequence=1,
        )
        second = _policy(
            [_rule("B", [PolicyRuleMember("service", "destination", _service("WEB", "tcp", 8080))])],
            name="Second",
            policy_sequence=2,
        )

        with pytest.raises(ValueError, match="Duplicate service definition with different values: WEB"):
            merge_policies([first, second])


class TestGenerationDiagnostics:
    @staticmethod
    def _record(level: int, message: str) -> logging.LogRecord:
        return logging.LogRecord("aerleon", level, __file__, 0, message, None, None)

    def test_log_records_are_classified(self):
        warnings, errors = _log_records_to_diagnostics(
            [
                self._record(logging.INFO, "ignored"),
                self._record(logging.WARNING, "Term_B is shaded by Term_A"),
                self._record(logging.WARNING, "  something odd  "),
                self._record(logging.ERROR, "broken"),
            ]
        )

        assert [(w.code, w.term_name, w.shaded_by_name, w.message) for w in warnings] == [
            ("shading", "Term_B", "Term_A", "Term_B is shaded by Term_A"),
            ("aerleon_warning", None, None, "something odd"),
        ]
        assert [(e.code, e.level, e.message) for e in errors] == [("aerleon_error", "error", "broken")]

    def test_dedupe_diagnostics_preserves_order(self):
        first = GenerationDiagnostic(source="rulio", level="warning", code="a", message="one")
        second = GenerationDiagnostic(source="rulio", level="warning", code="b", message="two")

        assert _dedupe_diagnostics([first, second, first]) == [first, second]

    def test_exception_without_message_uses_class_name(self):
        assert _exception_to_diagnostic(ValueError("")).message == "ValueError"
        assert _exception_to_diagnostic(ValueError(" boom ")).message == "boom"


class TestIcmpMapping:
    @pytest.mark.parametrize(
        ("protocol", "icmp_type", "expected"),
        [("icmp", 8, "echo-request"), (" ICMP ", 0, "echo-reply"), ("icmpv6", 128, "echo-request")],
    )
    def test_known_types(self, protocol, icmp_type, expected):
        assert get_aerleon_icmp_type(protocol, icmp_type) == expected

    @pytest.mark.parametrize(("protocol", "icmp_type"), [("tcp", 8), ("icmp", 99), ("icmpv6", 8)])
    def test_unknown_types_raise(self, protocol, icmp_type):
        with pytest.raises(ValueError):
            get_aerleon_icmp_type(protocol, icmp_type)

    @pytest.mark.parametrize("icmp_code", [0, 255])
    def test_code_bounds_accepted(self, icmp_code):
        assert get_aerleon_icmp_code(icmp_code) == str(icmp_code)

    @pytest.mark.parametrize("icmp_code", [-1, 256])
    def test_code_out_of_range_raises(self, icmp_code):
        with pytest.raises(ValueError, match="between 0 and 255"):
            get_aerleon_icmp_code(icmp_code)


class TestPlatformCapabilities:
    def test_vendor_lookup_is_normalized(self):
        assert get_platform_capabilities(" JUNIPER ") == get_platform_capabilities("juniper")

    def test_unknown_vendor_gets_defaults(self):
        assert get_platform_capabilities("unknown_vendor") == PlatformCapabilities()

    def test_unknown_capability_raises(self):
        with pytest.raises(ValueError, match="Unknown platform capability"):
            vendor_supports("juniper", "supports_teleportation")

    @pytest.mark.parametrize(
        ("vendor", "direction", "expected"),
        [("juniper", "IN", "in"), ("gce", "out", "EGRESS"), ("msmpc", "in", "ingress")],
    )
    def test_resolve_direction(self, vendor, direction, expected):
        assert resolve_platform_direction(vendor, direction) == expected

    @pytest.mark.parametrize(
        ("vendor", "direction", "message"),
        [("juniper", "both", "Unknown direction"), ("cisco", "in", "does not support")],
    )
    def test_resolve_direction_errors(self, vendor, direction, message):
        with pytest.raises(ValueError, match=message):
            resolve_platform_direction(vendor, direction)


IPV6_VENDORS = sorted(vendor for vendor, capabilities in PLATFORM_CAPABILITIES.items() if capabilities.supports_ipv6)

# Vendors whose target needs more than a filter name to generate at all.
IPV6_TEST_TARGET_OPTIONS = {
    "fortigate": ["from-zone", "internal", "to-zone", "external"],
    "paloalto": ["from-zone", "internal", "to-zone", "external"],
    "ipset": ["ACCEPT"],
    "iptables": ["ACCEPT"],
    "speedway": ["ACCEPT"],
    "nftables": ["INPUT"],
    "juniperevo": ["ingress"],
}


def _dual_stack_address(name: str = "Dual_Stack") -> Address:
    return Address(
        name=name,
        tenant_id=1,
        addr_type="network",
        ipv4_type="standard",
        ipv4Network="192.0.2.0/24",
        ipv6_type="standard",
        ipv6Network="2001:db8:1::/48",
    )


def _ipv6_address(name: str = "Only_V6") -> Address:
    return Address(name=name, tenant_id=1, addr_type="network", ipv6_type="standard", ipv6Network="2001:db8:1::/48")


def _address_policy(address: Address, vendor: str, target_options: list[str] | None = None, **kwargs) -> Policy:
    rule = _rule(
        "Web",
        [
            PolicyRuleMember("address", "destination", address),
            PolicyRuleMember("service", "destination", _service("WEB", "tcp", 80)),
        ],
    )
    return _policy([rule], vendor=vendor, target_options=target_options, **kwargs)


def _header_targets(policy: Policy) -> list[dict]:
    return [filter_config["header"]["targets"] for filter_config in policy.YAMLConfig["filters"]]


class TestIPv6TargetFamilies:
    @pytest.mark.parametrize("vendor", IPV6_VENDORS)
    def test_dual_stack_generates_both_families(self, vendor):
        policy = _address_policy(_dual_stack_address(), vendor, IPV6_TEST_TARGET_OPTIONS.get(vendor))

        result = generate_config(policy)

        assert result.success, [error.message for error in result.errors]
        generated_text = "\n".join(result.config.values())
        assert "192.0.2." in generated_text
        assert "2001:db8:1:" in generated_text

    @pytest.mark.parametrize(
        ("vendor", "target_options", "address", "expected_targets"),
        [
            ("juniper", None, _dual_stack_address(), ["Unit_Policy mixed"]),
            ("cisco", None, _dual_stack_address(), ["Unit_Policy mixed"]),
            ("cisco", None, _ipv6_address(), ["Unit_Policy inet6"]),
            ("cisco", None, _address("V4", "10.0.0.0/8"), ["Unit_Policy"]),
            ("juniperevo", ["ingress"], _dual_stack_address(), ["Unit_Policy mixed ingress"]),
            ("nftables", ["INPUT"], _dual_stack_address(), ["mixed INPUT"]),
            ("nftables", ["INPUT"], _address("V4", "10.0.0.0/8"), ["inet INPUT"]),
            (
                "paloalto",
                ["from-zone", "internal", "to-zone", "external"],
                _dual_stack_address(),
                ["from-zone internal to-zone external mixed"],
            ),
            ("iptables", ["ACCEPT"], _dual_stack_address(), ["Unit_Policy ACCEPT", "Unit_Policy ACCEPT inet6"]),
            ("iptables", ["ACCEPT"], _ipv6_address(), ["Unit_Policy ACCEPT inet6"]),
            ("windows_advfirewall", None, _dual_stack_address(), ["Unit_Policy", "Unit_Policy inet6"]),
            ("nvueapi", None, _dual_stack_address(), ["Unit_Policy inet", "Unit_Policy_ipv6 inet6"]),
        ],
    )
    def test_header_targets_follow_address_families(self, vendor, target_options, address, expected_targets):
        policy = _address_policy(address, vendor, target_options)

        assert _header_targets(policy) == [{vendor: target} for target in expected_targets]

    @pytest.mark.parametrize(
        ("allow_address", "deny_service", "expected_target"),
        [
            (_ipv6_address(), _service("SSH", "tcp", 22), "Unit_Policy mixed"),
            (_address("V4", "10.0.0.0/8"), _service("SSH", "tcp", 22), "Unit_Policy mixed"),
            (None, _service("SSH", "tcp", 22), "Unit_Policy mixed"),
            (None, _service("Ping", "icmp", icmp_type=8), "Unit_Policy"),
        ],
    )
    def test_rule_without_addresses_matches_both_families(self, allow_address, deny_service, expected_target):
        rules = []
        if allow_address is not None:
            rules.append(
                _rule(
                    "Allow_Web",
                    [
                        PolicyRuleMember("address", "destination", allow_address),
                        PolicyRuleMember("service", "destination", _service("WEB", "tcp", 80)),
                    ],
                    1,
                )
            )
        rules.append(
            _rule(
                "Deny_Anywhere",
                [PolicyRuleMember("service", "destination", deny_service)],
                len(rules) + 1,
                action="deny",
            )
        )

        policy = _policy(rules, vendor="cisco")

        assert _header_targets(policy) == [{"cisco": expected_target}]

    def test_rule_without_addresses_is_not_an_ipv6_error_for_vendor_without_ipv6(self):
        policy = _policy(
            [_rule("Deny_SSH", [PolicyRuleMember("service", "destination", _service("SSH", "tcp", 22))])],
            vendor="ciscoasa",
        )

        result = generate_config(policy)

        assert result.success, [error.message for error in result.errors]
        assert _header_targets(policy) == [{"ciscoasa": "Unit_Policy"}]

    def test_split_filters_share_the_same_terms(self):
        policy = _address_policy(_dual_stack_address(), "iptables", ["ACCEPT"])

        ipv4_filter, ipv6_filter = policy.YAMLConfig["filters"]
        assert ipv4_filter["terms"] == ipv6_filter["terms"]

    @pytest.mark.parametrize("vendor", IPV6_VENDORS)
    def test_target_templates_use_known_placeholders(self, vendor):
        template = PLATFORM_CAPABILITIES[vendor].target_template
        placeholders = {field_name for _, field_name, _, _ in string.Formatter().parse(template) if field_name}

        assert "af" in placeholders
        assert placeholders <= {"name", "options", "af"}

    def test_merge_keeps_both_filters_of_split_policies(self):
        first = _address_policy(_dual_stack_address(), "iptables", ["ACCEPT"], name="First", policy_sequence=1)
        second = _address_policy(_dual_stack_address(), "iptables", ["ACCEPT"], name="Second", policy_sequence=2)

        merged = merge_policies([first, second])

        assert _header_targets(merged) == [
            {"iptables": "First ACCEPT"},
            {"iptables": "First ACCEPT inet6"},
            {"iptables": "Second ACCEPT"},
            {"iptables": "Second ACCEPT inet6"},
        ]

    def test_unsupported_vendor_in_merged_policy_is_an_error(self):
        first = _address_policy(_address("V4", "10.0.0.0/8"), "ciscoasa", name="First", policy_sequence=1)
        second = _address_policy(_ipv6_address(), "ciscoasa", name="Second", policy_sequence=2)

        result = generate_config(merge_policies([first, second]))

        assert result.config is None
        assert [error.code for error in result.errors] == ["unsupported_ipv6"]
