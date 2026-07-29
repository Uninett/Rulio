ICMPV4_TYPE_MAP: dict[int, str] = {
    0: "echo-reply",
    3: "unreachable",
    4: "source-quench",
    5: "redirect",
    6: "alternate-address",
    8: "echo-request",
    9: "router-advertisement",
    10: "router-solicitation",
    11: "time-exceeded",
    12: "parameter-problem",
    13: "timestamp-request",
    14: "timestamp-reply",
    15: "information-request",
    16: "information-reply",
    17: "mask-request",
    18: "mask-reply",
    31: "conversion-error",
    32: "mobile-redirect",
}

ICMPV6_TYPE_MAP: dict[int, str] = {
    1: "destination-unreachable",
    2: "packet-too-big",
    3: "time-exceeded",
    4: "parameter-problem",
    128: "echo-request",
    129: "echo-reply",
    130: "multicast-listener-query",
    131: "multicast-listener-report",
    132: "multicast-listener-done",
    133: "router-solicit",
    134: "router-advertisement",
    135: "neighbor-solicit",
    136: "neighbor-advertisement",
    137: "redirect-message",
    138: "router-renumbering",
    139: "icmp-node-information-query",
    140: "icmp-node-information-response",
    141: "inverse-neighbor-discovery-solicitation",
    142: "inverse-neighbor-discovery-advertisement",
    143: "version-2-multicast-listener-report",
    144: "home-agent-address-discovery-request",
    145: "home-agent-address-discovery-reply",
    146: "mobile-prefix-solicitation",
    147: "mobile-prefix-advertisement",
    148: "certification-path-solicitation",
    149: "certification-path-advertisement",
    151: "multicast-router-advertisement",
    152: "multicast-router-solicitation",
    153: "multicast-router-termination",
}


def get_aerleon_icmp_type(protocol: str, icmp_type: int) -> str:
    normalized_protocol = protocol.strip().lower()

    if normalized_protocol == "icmp":
        mapping = ICMPV4_TYPE_MAP
    elif normalized_protocol == "icmpv6":
        mapping = ICMPV6_TYPE_MAP
    else:
        raise ValueError(f"ICMP type mapping requires protocol 'icmp' or 'icmpv6', got '{protocol}'")

    try:
        return mapping[icmp_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported ICMP type '{icmp_type}' for protocol '{normalized_protocol}'") from exc


def get_aerleon_icmp_code(icmp_code: int) -> str:
    if not 0 <= icmp_code <= 255:
        raise ValueError(f"ICMP code must be between 0 and 255, got {icmp_code}")

    return str(icmp_code)
