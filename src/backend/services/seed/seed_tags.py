from django.contrib.auth.models import User

from backend.objects.attributes.address import Address
from backend.objects.attributes.tag import Tag
from backend.services.helper_user_tenant import require_write_tenant
from backend.services.membership import add_tag_to_object
from backend.utils.logger import set_up_logger
from backend.services.attribute_objects.create_attribute_objects import create_tag
from backend.services.get import get_all_tags_from_tenant


logger = set_up_logger(__name__)


def seed_tags(actor: User, tenant_id: int) -> tuple[int, list[Tag]]:
    """
    Seed the database with a default tag set.

    Returns:
        tuple[int, list[Tag]]: Number of default tags processed and list of newly created tag objects.
    """
    require_write_tenant(actor, tenant_id)

    default_tags = [
        {"name": "default", "description": "General-purpose tag for seeded default objects."},
        {
            "name": "shared",
            "description": "Tag for objects intended to be reused across multiple rules, filters, devices, or interfaces.",
        },
        {"name": "temporary", "description": "Tag for temporary objects that may be removed or replaced later."},
        {"name": "deprecated", "description": "Tag for objects that should no longer be used for new configurations."},
        {
            "name": "critical",
            "description": "Tag for business-critical, security-critical, or operationally critical objects.",
        },
        {
            "name": "debugging",
            "description": "Tag for objects used for debugging, testing, troubleshooting, or observability.",
        },
        {"name": "production", "description": "Tag for objects intended for production environments."},
        {"name": "staging", "description": "Tag for objects intended for staging or pre-production environments."},
        {"name": "development", "description": "Tag for objects intended for development or lab environments."},
        {"name": "internal", "description": "Tag for objects intended for internal-only use within trusted networks."},
        {"name": "external", "description": "Tag for objects intended for external-facing or untrusted network use."},
        {"name": "inbound", "description": "Tag for objects commonly used in inbound traffic policies."},
        {"name": "outbound", "description": "Tag for objects commonly used in outbound traffic policies."},
        {
            "name": "east_west",
            "description": "Tag for objects commonly used in internal lateral or east-west traffic policies.",
        },
        {
            "name": "north_south",
            "description": "Tag for objects commonly used in north-south traffic crossing trust boundaries.",
        },
        {
            "name": "private_address_space",
            "description": "Tag for objects related to private or non-public address space.",
        },
        {
            "name": "public_address_space",
            "description": "Tag for objects related to public or globally reachable address space.",
        },
        {
            "name": "multicast",
            "description": "Tag for objects related to multicast traffic or multicast address ranges.",
        },
        {"name": "loopback", "description": "Tag for objects related to loopback traffic or loopback address ranges."},
        {
            "name": "link_local",
            "description": "Tag for objects related to link-local addressing or traffic confined to a local segment.",
        },
        {
            "name": "documentation",
            "description": "Tag for objects reserved for documentation, examples, or reference use.",
        },
        {
            "name": "transit",
            "description": "Tag for objects related to routed transit traffic or transit network use cases.",
        },
        {
            "name": "management",
            "description": "Tag for objects related to administrative access, device management, or control plane access.",
        },
        {
            "name": "monitoring",
            "description": "Tag for objects related to metrics, logging, telemetry, or observability.",
        },
        {
            "name": "infrastructure",
            "description": "Tag for core infrastructure objects such as DNS, DHCP, NTP, routing, and identity services.",
        },
        {
            "name": "authentication",
            "description": "Tag for objects related to authentication, authorization, directory, or identity services.",
        },
        {
            "name": "web",
            "description": "Tag for objects related to web applications, web publishing, or browser-based services.",
        },
        {"name": "database", "description": "Tag for objects related to database services and database connectivity."},
        {
            "name": "file_sharing",
            "description": "Tag for objects related to file sharing, storage access, or remote filesystem protocols.",
        },
        {
            "name": "vpn",
            "description": "Tag for objects related to VPN connectivity, secure tunnels, or encrypted overlays.",
        },
        {"name": "voice", "description": "Tag for objects related to voice, signaling, or multimedia communication."},
        {
            "name": "legacy",
            "description": "Tag for objects related to older, legacy, or less preferred protocols and services.",
        },
        {"name": "allow_list", "description": "Tag for objects commonly used in explicit allow-list style policies."},
        {"name": "deny_list", "description": "Tag for objects commonly used in explicit deny-list style policies."},
        {
            "name": "restricted",
            "description": "Tag for objects that should be limited to specific trusted sources, destinations, or contexts.",
        },
        {
            "name": "sensitive",
            "description": "Tag for objects related to sensitive systems, services, or traffic flows.",
        },
        {
            "name": "priority_1",
            "description": "Tag for objects with the highest priority in filtering or operational relevance.",
        },
        {
            "name": "priority_2",
            "description": "Tag for objects with medium priority in filtering or operational relevance.",
        },
        {
            "name": "priority_3",
            "description": "Tag for objects with lower priority in filtering or operational relevance.",
        },
        {"name": "border_router", "description": "Tag for objects associated with border router use cases."},
        {"name": "internal_router", "description": "Tag for objects associated with internal router use cases."},
        {"name": "external_router", "description": "Tag for objects associated with external router use cases."},
        {
            "name": "edge",
            "description": "Tag for objects associated with network edge, perimeter, or demarcation use cases.",
        },
        {"name": "dmz", "description": "Tag for objects associated with demilitarized zone segments or services."},
    ]

    existing_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    existing_tag_names = {tag.name for tag in existing_tags}

    created_count = 0
    created_tags = []

    for tag_data in default_tags:
        if tag_data["name"] in existing_tag_names:
            continue

        created_tags.append(
            create_tag(
                actor=actor,
                tenant_id=tenant_id,
                name=tag_data["name"],
                description=tag_data["description"],
            )
        )
        created_count += 1

    if created_count == len(default_tags):
        logger.info("All default tags were created. No duplicates existed.")
    elif created_count > 0:
        logger.warning("Some default tags already existed. Missing tags were created.")
    else:
        logger.warning("No default tags were created because they already all existed.")

    return len(default_tags), created_tags


def add_tags_to_default_addresses(
    actor: User,
    tenant_id: int,
    default_addresses: list[Address],
) -> None:
    """
    Add the correct tags to the seeded default addresses.
    """
    require_write_tenant(actor, tenant_id)

    tenant_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    tags_by_name: dict[str, Tag] = {tag.name: tag for tag in tenant_tags}

    addresses_by_name: dict[str, Address] = {address.name: address for address in default_addresses}

    address_tag_mappings: dict[str, list[str]] = {
        "Private_Class_A_IPv4_RFC1918": ["default", "private_address_space", "internal", "priority_1"],
        "Private_Class_B_IPv4_RFC1918": ["default", "private_address_space", "internal", "priority_1"],
        "Private_Class_C_IPv4_RFC1918": ["default", "private_address_space", "internal", "priority_1"],
        "Loopback_IPv4_RFC1122": ["default", "private_address_space", "loopback", "internal", "priority_2"],
        "LinkLocal_IPv4_RFC3927": ["default", "private_address_space", "link_local", "internal", "priority_2"],
        "CGNAT_IPv4_RFC6598": ["default", "private_address_space", "transit", "priority_2"],
        "Benchmark_Testing_IPv4_RFC2544": ["default", "debugging", "documentation", "development", "priority_3"],
        "Unspecified_IPv4_RFC1122": ["default", "transit", "restricted", "priority_2"],
        "Limited_Broadcast_IPv4_RFC919_RFC922": ["default", "restricted", "priority_2"],
        "Reserved_IPv4_RFC1112_RFC6890": ["default", "restricted", "priority_2"],
        "Multicast_IPv4_RFC1112": ["default", "multicast", "priority_2"],
        "Local_Subnet_Multicast_IPv4_RFC1112": ["default", "multicast", "link_local", "priority_2"],
        "TEST_NET_1_RFC5737": ["default", "documentation", "debugging", "development", "priority_3"],
        "TEST_NET_2_RFC5737": ["default", "documentation", "debugging", "development", "priority_3"],
        "TEST_NET_3_RFC5737": ["default", "documentation", "debugging", "development", "priority_3"],
        "Any_IPv4_RFC4632": ["default", "public_address_space", "external", "shared", "priority_1"],
        "ULA_IPv6_RFC4193": ["default", "private_address_space", "internal", "priority_1"],
        "ULA_Local_IPv6_RFC4193": ["default", "private_address_space", "internal", "priority_1"],
        "Loopback_IPv6_RFC4291": ["default", "private_address_space", "loopback", "internal", "priority_2"],
        "LinkLocal_IPv6_RFC4291": ["default", "private_address_space", "link_local", "internal", "priority_2"],
        "Unspecified_IPv6_RFC4291": ["default", "transit", "restricted", "priority_2"],
        "IPv4_Mapped_IPv6_RFC4291": ["default", "transit", "priority_3"],
        "Multicast_IPv6_RFC4291": ["default", "multicast", "priority_2"],
        "All_Nodes_Multicast_IPv6_RFC4291": ["default", "multicast", "link_local", "priority_2"],
        "All_Routers_Multicast_IPv6_RFC4291": ["default", "multicast", "link_local", "priority_2"],
        "NAT64_Well_Known_Prefix_IPv6_RFC6052": ["default", "transit", "priority_3"],
        "6to4_IPv6_RFC3056": ["default", "transit", "priority_3"],
        "Teredo_IPv6_RFC4380": ["default", "transit", "priority_3"],
        "Documentation_IPv6_RFC3849": ["default", "documentation", "debugging", "development", "priority_3"],
        "Any_IPv6_RFC4291": ["default", "public_address_space", "external", "shared", "priority_1"],
    }

    missing_tags = {
        tag_name
        for tag_names in address_tag_mappings.values()
        for tag_name in tag_names
        if tag_name not in tags_by_name
    }
    if missing_tags:
        raise ValueError(
            "Cannot tag default addresses because these tags are missing: " + ", ".join(sorted(missing_tags))
        )

    missing_addresses = [address_name for address_name in address_tag_mappings if address_name not in addresses_by_name]
    if missing_addresses:
        raise ValueError(
            "Cannot tag default addresses because these addresses are missing: " + ", ".join(sorted(missing_addresses))
        )

    for address_name, tag_names in address_tag_mappings.items():
        address = addresses_by_name[address_name]
        for tag_name in tag_names:
            add_tag_to_object(
                actor=actor,
                tenant_id=tenant_id,
                tag=tags_by_name[tag_name],
                obj=address,
            )

    logger.info("Added tags to all seeded default addresses.")
