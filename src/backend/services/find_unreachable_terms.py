import ipaddress

from backend.services.generate_config import Policy


def _parse_network_value(network_value):
    if isinstance(network_value, dict):
        if "address" in network_value:
            return ipaddress.ip_network(network_value["address"], strict=False)
        raise ValueError(f"Unsupported network value format: {network_value}")
    return ipaddress.ip_network(str(network_value), strict=False)


def _expand_network_references(network_definitions: dict, network_names: list[str] | None):
    if not network_names:
        return None

    expanded_networks = []
    for network_name in network_names:
        if network_name not in network_definitions:
            raise ValueError(f"Unknown network reference: {network_name}")

        values = network_definitions[network_name].get("values", [])
        for network_value in values:
            expanded_networks.append(_parse_network_value(network_value))

    return expanded_networks


def _parse_port_range(port_value: str | int):
    port_string = str(port_value)
    if "-" in port_string:
        start_port, end_port = port_string.split("-", 1)
        return int(start_port), int(end_port)
    port = int(port_string)
    return port, port


def _expand_service_references(service_definitions: dict, service_names: list[str] | None):
    if not service_names:
        return None

    expanded_protocols = set()
    expanded_ports = []

    for service_name in service_names:
        if service_name not in service_definitions:
            raise ValueError(f"Unknown service reference: {service_name}")

        entries = service_definitions[service_name]
        for entry in entries:
            protocol = entry.get("protocol")
            if protocol:
                expanded_protocols.add(protocol)

            if "port" in entry and entry["port"] is not None:
                expanded_ports.append(_parse_port_range(entry["port"]))

    return {
        "protocols": expanded_protocols if expanded_protocols else None,
        "ports": _merge_port_ranges(expanded_ports) if expanded_ports else None,
    }


def _normalize_networks(networks):
    if not networks:
        return None
    return _collapse_networks(networks)


def _normalize_term(term: dict, network_definitions: dict, service_definitions: dict) -> dict:
    protocol = term.get("protocol")

    return {
        "name": term["name"],
        "action": term.get("action"),
        "protocols": {protocol} if protocol else None,
        "source-address": _normalize_networks(
            _expand_network_references(network_definitions, term.get("source-address"))
        ),
        "destination-address": _normalize_networks(
            _expand_network_references(network_definitions, term.get("destination-address"))
        ),
        "source-port": _expand_service_references(service_definitions, term.get("source-port")),
        "destination-port": _expand_service_references(service_definitions, term.get("destination-port")),
    }


def expand_policy_terms(policy: Policy) -> list[dict]:
    network_definitions = policy.networks.get("networks", {})
    service_definitions = policy.services.get("services", {})
    terms = policy.YAMLConfig["filters"][0].get("terms", [])

    return [
        _normalize_term(
            term=term,
            network_definitions=network_definitions,
            service_definitions=service_definitions,
        )
        for term in terms
    ]


def _collapse_networks(networks):
    ipv4_networks = [network for network in networks if isinstance(network, ipaddress.IPv4Network)]
    ipv6_networks = [network for network in networks if isinstance(network, ipaddress.IPv6Network)]

    collapsed_networks = []

    if ipv4_networks:
        collapsed_networks.extend(ipaddress.collapse_addresses(ipv4_networks))

    if ipv6_networks:
        collapsed_networks.extend(ipaddress.collapse_addresses(ipv6_networks))

    return list(collapsed_networks)


def _merge_port_ranges(port_ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not port_ranges:
        return []

    sorted_port_ranges = sorted(port_ranges, key=lambda port_range: (port_range[0], port_range[1]))
    merged_port_ranges = [sorted_port_ranges[0]]

    for current_start, current_end in sorted_port_ranges[1:]:
        previous_start, previous_end = merged_port_ranges[-1]

        if current_start <= previous_end + 1:
            merged_port_ranges[-1] = (previous_start, max(previous_end, current_end))
        else:
            merged_port_ranges.append((current_start, current_end))

    return merged_port_ranges


def _network_contains(container_network, containee_network) -> bool:
    return type(container_network) is type(containee_network) and containee_network.subnet_of(container_network)


def _network_list_covers(previous_networks, current_networks) -> bool:
    if previous_networks is None:
        return True
    if current_networks is None:
        return previous_networks is None

    same_type_current_networks = {"ipv4": [], "ipv6": []}
    same_type_previous_networks = {"ipv4": [], "ipv6": []}

    for network in current_networks:
        if isinstance(network, ipaddress.IPv4Network):
            same_type_current_networks["ipv4"].append(network)
        else:
            same_type_current_networks["ipv6"].append(network)

    for network in previous_networks:
        if isinstance(network, ipaddress.IPv4Network):
            same_type_previous_networks["ipv4"].append(network)
        else:
            same_type_previous_networks["ipv6"].append(network)

    for family in ("ipv4", "ipv6"):
        for current_network in same_type_current_networks[family]:
            if not any(
                _network_contains(previous_network, current_network)
                for previous_network in same_type_previous_networks[family]
            ):
                return False

    return True


def _port_range_contains(container_port_range, containee_port_range) -> bool:
    return container_port_range[0] <= containee_port_range[0] and container_port_range[1] >= containee_port_range[1]


def _port_list_covers(previous_ports, current_ports) -> bool:
    if previous_ports is None:
        return True
    if current_ports is None:
        return previous_ports is None

    for current_port_range in current_ports:
        if not any(
            _port_range_contains(previous_port_range, current_port_range) for previous_port_range in previous_ports
        ):
            return False
    return True


def _protocol_set_covers(previous_protocols, current_protocols) -> bool:
    if previous_protocols is None:
        return True
    if current_protocols is None:
        return previous_protocols is None
    return current_protocols.issubset(previous_protocols)


def _service_match_covers(previous_service_match, current_service_match) -> bool:
    previous_protocols = previous_service_match["protocols"] if previous_service_match else None
    current_protocols = current_service_match["protocols"] if current_service_match else None

    if not _protocol_set_covers(previous_protocols, current_protocols):
        return False

    previous_ports = previous_service_match["ports"] if previous_service_match else None
    current_ports = current_service_match["ports"] if current_service_match else None

    return _port_list_covers(previous_ports, current_ports)


def _address_constraint_present(term: dict) -> bool:
    return term["source-address"] is not None or term["destination-address"] is not None


def _port_constraint_present(term: dict) -> bool:
    return term["source-port"] is not None or term["destination-port"] is not None


def _same_action(previous_term: dict, current_term: dict) -> bool:
    return previous_term.get("action") == current_term.get("action")


def _build_shadow_reason(previous_term: dict, current_term: dict) -> str:
    reasons = []

    if _same_action(previous_term, current_term):
        reasons.append("same action")
    else:
        reasons.append("different action but earlier first-match term still prevents later match")

    if _protocol_set_covers(previous_term["protocols"], current_term["protocols"]):
        reasons.append("protocol fully covered")

    if _network_list_covers(previous_term["source-address"], current_term["source-address"]):
        reasons.append("source-address fully covered")

    if _network_list_covers(previous_term["destination-address"], current_term["destination-address"]):
        reasons.append("destination-address fully covered")

    previous_source_ports = previous_term["source-port"]["ports"] if previous_term["source-port"] else None
    current_source_ports = current_term["source-port"]["ports"] if current_term["source-port"] else None
    if _port_list_covers(previous_source_ports, current_source_ports):
        reasons.append("source-port fully covered")

    previous_destination_ports = (
        previous_term["destination-port"]["ports"] if previous_term["destination-port"] else None
    )
    current_destination_ports = current_term["destination-port"]["ports"] if current_term["destination-port"] else None
    if _port_list_covers(previous_destination_ports, current_destination_ports):
        reasons.append("destination-port fully covered")

    return ", ".join(reasons)


def term_covers(previous_term: dict, current_term: dict) -> bool:
    if not _protocol_set_covers(previous_term["protocols"], current_term["protocols"]):
        return False

    if not _network_list_covers(previous_term["source-address"], current_term["source-address"]):
        return False

    if not _network_list_covers(previous_term["destination-address"], current_term["destination-address"]):
        return False

    if not _service_match_covers(previous_term["source-port"], current_term["source-port"]):
        return False

    if not _service_match_covers(previous_term["destination-port"], current_term["destination-port"]):
        return False

    return True


def find_potentially_unreachable_terms(policy: Policy) -> list[dict]:
    expanded_terms = expand_policy_terms(policy)
    unreachable_terms = []

    for current_index, current_term in enumerate(expanded_terms):
        for previous_index, previous_term in enumerate(expanded_terms[:current_index]):
            if not term_covers(previous_term, current_term):
                continue

            unreachable_terms.append(
                {
                    "term_name": current_term["name"],
                    "shadowed_by": previous_term["name"],
                    "shadowed_by_index": previous_index,
                    "term_index": current_index,
                    "current_action": current_term.get("action"),
                    "shadowing_action": previous_term.get("action"),
                    "reason": _build_shadow_reason(previous_term, current_term),
                    "has_address_constraints": _address_constraint_present(current_term),
                    "has_port_constraints": _port_constraint_present(current_term),
                }
            )
            break

    return unreachable_terms
