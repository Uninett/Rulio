from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class PlatformCapabilities:
    supports_neutral_port: bool = False
    supports_source_port: bool = True
    supports_icmp_type: bool = True
    supports_icmp_code: bool = False
    supports_direction: bool = False
    direction_tokens: Mapping[str, str] | None = None


PLATFORM_CAPABILITIES: dict[str, PlatformCapabilities] = {
    "arista_tp": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "arista": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "aruba": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "brocade": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "cisco": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "ciscoasa": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "cisconx": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "ciscoxr": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "fortigate": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "gce": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "INGRESS", "out": "EGRESS"},
    ),
    "ipset": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "iptables": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "juniper": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "juniperevo": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "msmpc": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "ingress", "out": "egress"},
    ),
    "srx": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "k8s": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "INGRESS", "out": "EGRESS"},
    ),
    "nftables": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nokiasrl": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nsxv": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nvueapi": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nsxt": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "packetfilter": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "paloalto": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "pcapfilter": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "proxmox": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "speedway": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "srxlo": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "windows_advfirewall": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "windows_ipsec": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
}


def get_platform_capabilities(vendor: str) -> PlatformCapabilities:
    normalized_vendor = vendor.strip().lower()
    return PLATFORM_CAPABILITIES.get(normalized_vendor, PlatformCapabilities())


def vendor_supports(vendor: str, capability: str) -> bool:
    capabilities = get_platform_capabilities(vendor)

    try:
        return bool(getattr(capabilities, capability))
    except AttributeError as exc:
        raise ValueError(f"Unknown platform capability '{capability}'") from exc


def resolve_platform_direction(vendor: str, direction: str) -> str:
    normalized_direction = direction.strip().lower()
    if normalized_direction not in {"in", "out"}:
        raise ValueError(f"Unknown direction '{direction}'. Expected 'in' or 'out'.")

    capabilities = get_platform_capabilities(vendor)

    if not capabilities.supports_direction:
        raise ValueError(f"Vendor '{vendor}' does not support simple in/out direction-aware generation.")

    if not capabilities.direction_tokens:
        raise ValueError(f"Vendor '{vendor}' does not define a direction token mapping.")

    try:
        return capabilities.direction_tokens[normalized_direction]
    except KeyError as exc:
        raise ValueError(f"Vendor '{vendor}' does not define a token for direction '{normalized_direction}'.") from exc
