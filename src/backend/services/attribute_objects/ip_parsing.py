from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network


def can_enable_automatic_ip_auto(
    ip_auto: str,
    ip_type: str,
    ipNetwork: IPv4Network | IPv6Network | None,
    ipAddress_start: IPv4Address | IPv6Address | None,
    ipAddress_end: IPv4Address | IPv6Address | None,
) -> bool:
    """Determine if automatic IP assignment can be enabled based on the current IP configuration."""
    if ip_type == "remove":
        return False
    if not ip_auto:
        return False
    elif ip_type is not None or ipNetwork is not None or ipAddress_start is not None or ipAddress_end is not None:
        raise ValueError("Cannot enable automatic IP assignment when IP address fields are manually specified.")
    return True


def parse_ipv4_auto(
    ipv4_auto: str,
) -> tuple[str, IPv4Network | None, IPv4Address | None, IPv4Address | None, str]:
    """
    Parse an ipv4_auto string (CIDR or 'start-end' range) into its component parts.

    Returns a tuple containing:
    - The IPv4_type field ("standard" or "custom_range")
    - The IPv4 network if applicable, otherwise None
    - The starting IPv4 address if applicable, otherwise None
    - The ending IPv4 address if applicable, otherwise None
    - The detected IPv4 address type ("host", "network", or "range")
    """
    ipv4_auto = ipv4_auto.strip()

    if "-" in ipv4_auto:
        parts = ipv4_auto.split("-")
        if len(parts) != 2:
            raise ValueError("Invalid IPv4 range format. Use 'start-end' without CIDR notation.")

        ipv4Address_start_str, ipv4Address_end_str = (part.strip() for part in parts)

        if "/" in ipv4Address_start_str or "/" in ipv4Address_end_str:
            raise ValueError("Invalid IPv4 range format. Use 'start-end' without CIDR notation.")

        ipv4Address_start = IPv4Address(ipv4Address_start_str)
        ipv4Address_end = IPv4Address(ipv4Address_end_str)
        return "custom_range", None, ipv4Address_start, ipv4Address_end, "range"

    ipv4Network = IPv4Network(ipv4_auto, strict=False)
    detected_ipv4_addr_type = "host" if ipv4Network.prefixlen == 32 else "network"
    return "standard", ipv4Network, None, None, detected_ipv4_addr_type


def parse_ipv6_auto(
    ipv6_auto: str,
) -> tuple[str, IPv6Network | None, IPv6Address | None, IPv6Address | None, str]:
    """Parse an ipv6_auto string (CIDR or 'start-end' range) into its component parts."""
    ipv6_auto = ipv6_auto.strip()

    if "-" in ipv6_auto:
        parts = ipv6_auto.split("-")
        if len(parts) != 2:
            raise ValueError("Invalid IPv6 range format. Use 'start-end' without CIDR notation.")

        ipv6Address_start_str, ipv6Address_end_str = (part.strip() for part in parts)

        if "/" in ipv6Address_start_str or "/" in ipv6Address_end_str:
            raise ValueError("Invalid IPv6 range format. Use 'start-end' without CIDR notation.")

        ipv6Address_start = IPv6Address(ipv6Address_start_str)
        ipv6Address_end = IPv6Address(ipv6Address_end_str)
        return "custom_range", None, ipv6Address_start, ipv6Address_end, "range"

    ipv6Network = IPv6Network(ipv6_auto, strict=False)
    detected_ipv6_addr_type = "host" if ipv6Network.prefixlen == 128 else "network"
    return "standard", ipv6Network, None, None, detected_ipv6_addr_type


def get_addr_type(
    ipv4_type: str | None = None,
    ipv6_type: str | None = None,
    detected_ipv4_addr_type: str | None = None,
    detected_ipv6_addr_type: str | None = None,
) -> str | None:
    """Determine the address type based on IPv4 and IPv6 types and detected address types."""

    if ipv4_type == "custom_range" and detected_ipv4_addr_type != "range":
        raise ValueError(f"Invalid IPv4 custom range. Detected IPv4 type is {detected_ipv4_addr_type}")
    if ipv6_type == "custom_range" and detected_ipv6_addr_type != "range":
        raise ValueError(f"Invalid IPv6 custom range. Detected IPv6 type is {detected_ipv6_addr_type}")

    if detected_ipv4_addr_type and detected_ipv6_addr_type:
        # If either address is a host, both must be hosts.
        if (
            "host" in (detected_ipv4_addr_type, detected_ipv6_addr_type)
            and detected_ipv4_addr_type != detected_ipv6_addr_type
        ):
            raise TypeError(
                f"Address type mismatch: IPv4 type '{detected_ipv4_addr_type}' and IPv6 type "
                f"'{detected_ipv6_addr_type}' need to match when either is a host address."
            )
        # If IPv4 is a range and IPv6 is a network, the address will be classified as a range.
        if detected_ipv4_addr_type == "range":
            return "range"

    return detected_ipv4_addr_type or detected_ipv6_addr_type
