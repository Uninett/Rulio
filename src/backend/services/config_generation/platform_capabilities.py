from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformCapabilities:
    supports_neutral_port: bool = False
    supports_source_port: bool = True
    supports_icmp_type: bool = True
    supports_icmp_code: bool = False


PLATFORM_CAPABILITIES: dict[str, PlatformCapabilities] = {
    "arista_tp": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "arista": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "aruba": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        supports_icmp_type=False,
        supports_icmp_code=False,
    ),
    "brocade": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "cisco": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "ciscoasa": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "cisconx": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "ciscoxr": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "fortigate": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "gce": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=False,
        supports_icmp_code=False,
    ),
    "ipset": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "iptables": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "juniper": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "juniperevo": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "msmpc": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "srx": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "k8s": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        supports_icmp_type=False,
        supports_icmp_code=False,
    ),
    "nftables": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "nokiasrl": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "nsxv": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "nvueapi": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "nsxt": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "packetfilter": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "paloalto": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "pcapfilter": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "proxmox": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "speedway": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "srxlo": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=True,
    ),
    "windows_advfirewall": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
    ),
    "windows_ipsec": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        supports_icmp_type=True,
        supports_icmp_code=False,
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