from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

IPv6Mode = Literal["none", "mixed", "split"]


@dataclass(frozen=True, slots=True)
class PlatformCapabilities:
    supports_neutral_port: bool = False
    supports_source_port: bool = True
    ipv6_mode: IPv6Mode = "none"
    ipv4_keyword: str | None = None
    ipv6_keyword: str = "inet6"
    ipv6_filter_suffix: str = ""
    target_template: str = "{name} {af} {options}"
    supports_icmp_type: bool = True
    supports_icmp_code: bool = False
    supports_direction: bool = False
    direction_tokens: Mapping[str, str] | None = None

    @property
    def supports_ipv6(self) -> bool:
        return self.ipv6_mode != "none"


PLATFORM_CAPABILITIES: dict[str, PlatformCapabilities] = {
    "arista_tp": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "arista": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "aruba": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        ipv6_mode="split",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "brocade": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "cisco": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "ciscoasa": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "cisconx": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "ciscoxr": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "fortigate": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{options} {af}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    # Cloud Armor only matches source addresses, so rules with protocols, ports or destinations are refused by Aerleon.
    # Its header has no filter name: the first option is the address family, so "inet" is always written for IPv4.
    "cloudarmor": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        ipv6_mode="mixed",
        ipv4_keyword="inet",
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "gce": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "INGRESS", "out": "EGRESS"},
    ),
    # The policy name (the filter name) must be lowercase letters, digits and dashes, starting with a letter.
    # Aerleon refuses source ports and the tcp-established option for hierarchical firewalls.
    "gcp_hf": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        # Unsure: Aerleon renders inet6/mixed, but GCP only accepts IPv6 with the "ga" API version option, which Rulio
        # does not add. Kept IPv4 only, like gce.
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "INGRESS", "out": "EGRESS"},
    ),
    "ipset": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="split",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {options} {af}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "iptables": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="split",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {options} {af}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "juniper": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "juniperevo": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "msmpc": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "ingress", "out": "egress"},
    ),
    "srx": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "k8s": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=False,
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "INGRESS", "out": "EGRESS"},
    ),
    "nftables": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword="inet",
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nokiasrl": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nsxv": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword="inet",
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nvueapi": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="split",
        ipv4_keyword="inet",
        ipv6_keyword="inet6",
        ipv6_filter_suffix="_ipv6",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "nsxt": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword="inet",
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    # OpenConfig ACLs have no ICMP type or code match (Aerleon removes icmp-type), and no direction in the header.
    "openconfig": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    # SONiC is Aerleon's OpenConfig generator with a different tcp-established output, so it has the same values.
    "sonic": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=False,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "packetfilter": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "paloalto": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{options} {af}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "pcap": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "proxmox": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="none",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=False,
        direction_tokens=None,
    ),
    "speedway": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="split",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {options} {af}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=False,
        direction_tokens=None,
    ),
    "srxlo": PlatformCapabilities(
        supports_neutral_port=True,
        supports_source_port=True,
        ipv6_mode="mixed",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{name} {af} {options}",
        supports_icmp_type=True,
        supports_icmp_code=True,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
    "windows_advfirewall": PlatformCapabilities(
        supports_neutral_port=False,
        supports_source_port=True,
        ipv6_mode="split",
        ipv4_keyword=None,
        ipv6_keyword="inet6",
        ipv6_filter_suffix="",
        target_template="{options} {af}",
        supports_icmp_type=True,
        supports_icmp_code=False,
        supports_direction=True,
        direction_tokens={"in": "in", "out": "out"},
    ),
}


# The device form picks a vendor first, then one of its platforms. Each platform key belongs to exactly one vendor.
# Vendor label -> (platform key, platform label), with vendors in alphabetical order.
# Platform labels follow the generator titles in the Aerleon docs, with spaces between words
# (https://aerleon.readthedocs.io/en/latest/reference/generators/). They are shown in the device form and table.
PLATFORM_VENDORS: dict[str, tuple[tuple[str, str], ...]] = {
    "Arista": (("arista", "Arista"), ("arista_tp", "Arista Traffic-Policy")),
    "Aruba": (("aruba", "Aruba"),),
    "Brocade": (("brocade", "Brocade"),),
    "Cisco": (
        ("cisco", "Cisco"),
        ("ciscoasa", "Cisco ASA"),
        ("cisconx", "Cisco NX"),
        ("ciscoxr", "Cisco XR"),
    ),
    "Fortinet": (("fortigate", "FortiGate"),),
    "Google Cloud": (("gce", "GCE"), ("gcp_hf", "GCP Hierarchical Firewall"), ("cloudarmor", "Cloud Armor")),
    "Juniper": (
        ("juniper", "Juniper"),
        ("juniperevo", "Juniper EVO"),
        ("msmpc", "Juniper MSMPC"),
        ("srx", "Juniper SRX"),
        ("srxlo", "Juniper SRX Loopback"),
    ),
    "Kubernetes": (("k8s", "K8s"),),
    "Linux": (
        ("iptables", "Iptables"),
        ("ipset", "Ipset"),
        ("nftables", "Nftables"),
        ("speedway", "Speedway"),
    ),
    "Nokia": (("nokiasrl", "Nokia SR Linux"),),
    "NVIDIA": (("nvueapi", "NVUE API"),),
    "OpenBSD": (("packetfilter", "Packet Filter"),),
    "OpenConfig": (("openconfig", "OpenConfig"),),
    "Palo Alto Networks": (("paloalto", "Palo Alto Firewall"),),
    "pcap filter": (("pcap", "Pcap Filter"),),
    "Proxmox": (("proxmox", "Proxmox"),),
    "SONiC": (("sonic", "SONiC"),),
    "VMware": (("nsxv", "NSXv"), ("nsxt", "NSXt")),
    "Windows": (("windows_advfirewall", "Windows Advanced Firewall"),),
}


# The vendor label of a platform key, or None for an unknown platform.
def get_platform_vendor(platform: str) -> str | None:
    for vendor, platforms in PLATFORM_VENDORS.items():
        if any(key == platform for key, _label in platforms):
            return vendor
    return None


# The display label of a platform key, such as "Juniper SRX" for "srx". Unknown platforms are shown as stored.
def get_platform_label(platform: str) -> str:
    for platforms in PLATFORM_VENDORS.values():
        for key, label in platforms:
            if key == platform:
                return label
    return platform


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
