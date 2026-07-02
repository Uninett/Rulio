from django.contrib.auth.models import User

from backend.objects.attributes.address import Address
from backend.objects.attributes.service import Service
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


def add_tags_to_default_services(
    actor: User,
    tenant_id: int,
    default_services: list[Service],
) -> None:
    """
    Add the correct tags to the seeded default services.
    """
    require_write_tenant(actor, tenant_id)

    tenant_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    tags_by_name: dict[str, Tag] = {tag.name: tag for tag in tenant_tags}
    services_by_name: dict[str, Service] = {service.name: service for service in default_services}

    service_tag_mappings: dict[str, list[str]] = {
        "ICMP_RFC792": ["default", "infrastructure", "monitoring", "debugging", "priority_1"],
        "ICMPv6_RFC4443": ["default", "infrastructure", "monitoring", "debugging", "priority_1"],
        "GRE_RFC2784": ["default", "vpn", "transit", "restricted", "priority_3"],
        "ESP_RFC4303": ["default", "vpn", "restricted", "priority_3"],
        "AH_RFC4302": ["default", "vpn", "restricted", "priority_3"],
        "IP_RFC791": ["default", "shared", "priority_1"],
        "HTTP_TCP_RFC2616_RFC9110": ["default", "web", "external", "outbound", "priority_1"],
        "HTTPS_TCP_RFC2818_RFC9110": ["default", "web", "external", "outbound", "priority_1"],
        "HTTP_Alternate_TCP": ["default", "web", "external", "outbound", "priority_2"],
        "HTTPS_Alternate_TCP": ["default", "web", "external", "management", "priority_2"],
        "DNS_UDP_RFC1034_RFC1035": ["default", "infrastructure", "internal", "priority_1"],
        "DNS_TCP_RFC1034_RFC1035": ["default", "infrastructure", "internal", "priority_1"],
        "MDNS_UDP_RFC6762": ["default", "infrastructure", "multicast", "link_local", "priority_3"],
        "SSH_TCP_RFC4251": ["default", "management", "restricted", "sensitive", "priority_1"],
        "Telnet_TCP_RFC854": ["default", "management", "legacy", "restricted", "priority_3"],
        "RDP_TCP": ["default", "management", "restricted", "sensitive", "priority_2"],
        "WinRM_HTTP_TCP": ["default", "management", "restricted", "sensitive", "priority_2"],
        "WinRM_HTTPS_TCP": ["default", "management", "restricted", "sensitive", "priority_2"],
        "FTP_Control_TCP_RFC959": ["default", "legacy", "file_sharing", "priority_3"],
        "FTP_Data_TCP_RFC959": ["default", "legacy", "file_sharing", "priority_3"],
        "SFTP_TCP": ["default", "file_sharing", "management", "restricted", "priority_2"],
        "TFTP_UDP_RFC1350": ["default", "legacy", "file_sharing", "restricted", "priority_3"],
        "SMTP_TCP_RFC5321": ["default", "external", "outbound", "priority_2"],
        "SMTP_Submission_TCP_RFC6409": ["default", "external", "outbound", "priority_2"],
        "SMTPS_TCP": ["default", "external", "outbound", "priority_2"],
        "POP3_TCP_RFC1939": ["default", "legacy", "priority_3"],
        "POP3S_TCP": ["default", "priority_3"],
        "IMAP_TCP_RFC3501": ["default", "legacy", "priority_3"],
        "IMAPS_TCP": ["default", "priority_3"],
        "LDAP_TCP_RFC4511": ["default", "authentication", "infrastructure", "internal", "restricted", "priority_2"],
        "LDAPS_TCP": ["default", "authentication", "infrastructure", "internal", "restricted", "priority_2"],
        "Kerberos_TCP_RFC4120": ["default", "authentication", "infrastructure", "internal", "restricted", "priority_2"],
        "Kerberos_UDP_RFC4120": ["default", "authentication", "infrastructure", "internal", "restricted", "priority_2"],
        "RADIUS_Auth_UDP_RFC2865": ["default", "authentication", "infrastructure", "restricted", "priority_2"],
        "RADIUS_Acct_UDP_RFC2866": ["default", "authentication", "infrastructure", "restricted", "priority_2"],
        "DHCP_Server_UDP_RFC2131": ["default", "infrastructure", "internal", "priority_1"],
        "DHCP_Client_UDP_RFC2131": ["default", "infrastructure", "internal", "priority_1"],
        "NTP_UDP_RFC5905": ["default", "infrastructure", "internal", "priority_1"],
        "SNMP_UDP_RFC3411": ["default", "monitoring", "management", "restricted", "priority_2"],
        "SNMP_Trap_UDP_RFC3411": ["default", "monitoring", "management", "restricted", "priority_2"],
        "Syslog_UDP_RFC5424": ["default", "monitoring", "priority_2"],
        "Syslog_TCP_RFC6587": ["default", "monitoring", "priority_2"],
        "SMB_TCP": ["default", "file_sharing", "internal", "restricted", "priority_2"],
        "NetBIOS_NS_UDP": ["default", "legacy", "file_sharing", "internal", "priority_3"],
        "NetBIOS_DGM_UDP": ["default", "legacy", "file_sharing", "internal", "priority_3"],
        "NetBIOS_SSN_TCP": ["default", "legacy", "file_sharing", "internal", "priority_3"],
        "NFS_TCP_RFC7530": ["default", "file_sharing", "internal", "restricted", "priority_2"],
        "NFS_UDP": ["default", "legacy", "file_sharing", "internal", "priority_3"],
        "MySQL_TCP": ["default", "database", "internal", "restricted", "sensitive", "priority_2"],
        "PostgreSQL_TCP": ["default", "database", "internal", "restricted", "sensitive", "priority_2"],
        "MSSQL_TCP": ["default", "database", "internal", "restricted", "sensitive", "priority_2"],
        "IKE_UDP_RFC7296": ["default", "vpn", "restricted", "priority_3"],
        "IPsec_NAT_T_UDP_RFC3948": ["default", "vpn", "restricted", "priority_3"],
        "L2TP_UDP_RFC2661": ["default", "vpn", "legacy", "restricted", "priority_3"],
        "OpenVPN_TCP": ["default", "vpn", "restricted", "priority_3"],
        "OpenVPN_UDP": ["default", "vpn", "restricted", "priority_3"],
        "WireGuard_UDP": ["default", "vpn", "restricted", "priority_2"],
        "SIP_TCP_RFC3261": ["default", "voice", "priority_3"],
        "SIP_UDP_RFC3261": ["default", "voice", "priority_3"],
        "SIPS_TCP_RFC3261": ["default", "voice", "priority_3"],
        "Prometheus_TCP": ["default", "monitoring", "debugging", "priority_2"],
        "Grafana_TCP": ["default", "monitoring", "debugging", "web", "priority_2"],
        "Any_TCP": ["default", "shared", "priority_1"],
        "Any_UDP": ["default", "shared", "priority_1"],
    }

    missing_tags = {
        tag_name
        for tag_names in service_tag_mappings.values()
        for tag_name in tag_names
        if tag_name not in tags_by_name
    }
    if missing_tags:
        raise ValueError(
            "Cannot tag default services because these tags are missing: " + ", ".join(sorted(missing_tags))
        )

    missing_services = [service_name for service_name in service_tag_mappings if service_name not in services_by_name]
    if missing_services:
        raise ValueError(
            "Cannot tag default services because these services are missing: " + ", ".join(sorted(missing_services))
        )

    for service_name, tag_names in service_tag_mappings.items():
        service = services_by_name[service_name]
        for tag_name in tag_names:
            add_tag_to_object(
                actor=actor,
                tenant_id=tenant_id,
                tag=tags_by_name[tag_name],
                obj=service,
            )

    logger.info("Added tags to all seeded default services.")


def add_tags_to_default_address_groups(
    actor: User,
    tenant_id: int,
    default_address_groups: list,
) -> None:
    """
    Add the correct tags to the seeded default address groups.
    """
    require_write_tenant(actor, tenant_id)

    tenant_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    tags_by_name: dict[str, Tag] = {tag.name: tag for tag in tenant_tags}
    address_groups_by_name = {address_group.name: address_group for address_group in default_address_groups}

    address_group_tag_mappings: dict[str, list[str]] = {
        "Private_And_Local_Use_Addresses": [
            "default",
            "private_address_space",
            "internal",
            "restricted",
            "priority_1",
        ],
        "Invalid_Transit_Addresses": [
            "default",
            "transit",
            "deny_list",
            "restricted",
            "priority_1",
        ],
        "Documentation_And_Test_Addresses": [
            "default",
            "documentation",
            "debugging",
            "development",
            "deny_list",
            "priority_3",
        ],
        "Multicast_Addresses": [
            "default",
            "multicast",
            "restricted",
            "priority_2",
        ],
        "IPv6_Transition_And_Translation_Addresses": [
            "default",
            "transit",
            "restricted",
            "priority_2",
        ],
    }

    missing_tags = {
        tag_name
        for tag_names in address_group_tag_mappings.values()
        for tag_name in tag_names
        if tag_name not in tags_by_name
    }
    if missing_tags:
        raise ValueError(
            "Cannot tag default address groups because these tags are missing: " + ", ".join(sorted(missing_tags))
        )

    missing_address_groups = [
        address_group_name
        for address_group_name in address_group_tag_mappings
        if address_group_name not in address_groups_by_name
    ]
    if missing_address_groups:
        raise ValueError(
            "Cannot tag default address groups because these address groups are missing: "
            + ", ".join(sorted(missing_address_groups))
        )

    for address_group_name, tag_names in address_group_tag_mappings.items():
        address_group = address_groups_by_name[address_group_name]
        for tag_name in tag_names:
            add_tag_to_object(
                actor=actor,
                tenant_id=tenant_id,
                tag=tags_by_name[tag_name],
                obj=address_group,
            )

    logger.info("Added tags to all seeded default address groups.")


def add_tags_to_default_service_groups(
    actor: User,
    tenant_id: int,
    default_service_groups: list,
) -> None:
    """
    Add the correct tags to the seeded default service groups.
    """
    require_write_tenant(actor, tenant_id)

    tenant_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    tags_by_name: dict[str, Tag] = {tag.name: tag for tag in tenant_tags}
    service_groups_by_name = {service_group.name: service_group for service_group in default_service_groups}

    service_group_tag_mappings: dict[str, list[str]] = {
        "Common_Infrastructure_Client_Services": [
            "default",
            "infrastructure",
            "internal",
            "allow_list",
            "priority_1",
        ],
        "Common_Web_Access_Services": [
            "default",
            "web",
            "external",
            "allow_list",
            "priority_1",
        ],
        "Restricted_Administrative_Access_Services": [
            "default",
            "management",
            "restricted",
            "sensitive",
            "priority_1",
        ],
        "Restricted_Internal_Identity_Services": [
            "default",
            "authentication",
            "infrastructure",
            "internal",
            "restricted",
            "priority_2",
        ],
        "Restricted_Internal_File_Sharing_Services": [
            "default",
            "file_sharing",
            "internal",
            "restricted",
            "priority_2",
        ],
        "Restricted_Database_Services": [
            "default",
            "database",
            "internal",
            "restricted",
            "sensitive",
            "priority_2",
        ],
        "Restricted_Monitoring_And_Logging_Services": [
            "default",
            "monitoring",
            "management",
            "debugging",
            "restricted",
            "priority_2",
        ],
        "Deny_Legacy_Insecure_Services": [
            "default",
            "legacy",
            "deny_list",
            "restricted",
            "priority_3",
        ],
        "Deny_Tunneling_And_VPN_Services": [
            "default",
            "vpn",
            "deny_list",
            "restricted",
            "priority_3",
        ],
        "Deny_Voice_And_Signaling_Services": [
            "default",
            "voice",
            "deny_list",
            "restricted",
            "priority_3",
        ],
        "Deny_Local_Link_Resolution_Services": [
            "default",
            "multicast",
            "link_local",
            "deny_list",
            "restricted",
            "priority_3",
        ],
    }

    missing_tags = {
        tag_name
        for tag_names in service_group_tag_mappings.values()
        for tag_name in tag_names
        if tag_name not in tags_by_name
    }
    if missing_tags:
        raise ValueError(
            "Cannot tag default service groups because these tags are missing: " + ", ".join(sorted(missing_tags))
        )

    missing_service_groups = [
        service_group_name
        for service_group_name in service_group_tag_mappings
        if service_group_name not in service_groups_by_name
    ]
    if missing_service_groups:
        raise ValueError(
            "Cannot tag default service groups because these service groups are missing: "
            + ", ".join(sorted(missing_service_groups))
        )

    for service_group_name, tag_names in service_group_tag_mappings.items():
        service_group = service_groups_by_name[service_group_name]
        for tag_name in tag_names:
            add_tag_to_object(
                actor=actor,
                tenant_id=tenant_id,
                tag=tags_by_name[tag_name],
                obj=service_group,
            )

    logger.info("Added tags to all seeded default service groups.")


def add_tags_to_default_rules(
    actor: User,
    tenant_id: int,
    default_rules: list,
) -> None:
    """
    Add the correct tags to the seeded default rules.
    """
    require_write_tenant(actor, tenant_id)

    tenant_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    tags_by_name: dict[str, Tag] = {tag.name: tag for tag in tenant_tags}
    rules_by_name = {rule.name: rule for rule in default_rules}

    rule_tag_mappings: dict[str, list[str]] = {
        "Allow_Private_And_Local_Use_Addresses_To_Common_Infrastructure_Client_Services": [
            "default",
            "internal",
            "infrastructure",
            "allow_list",
            "priority_1",
        ],
        "Allow_Private_And_Local_Use_Addresses_To_Common_Web_Access_Services": [
            "default",
            "internal",
            "web",
            "allow_list",
            "priority_1",
        ],
        "Allow_Private_And_Local_Use_Addresses_To_Restricted_Administrative_Access_Services": [
            "default",
            "internal",
            "management",
            "restricted",
            "allow_list",
            "priority_1",
        ],
        "Allow_Private_And_Local_Use_Addresses_To_Restricted_Internal_Identity_Services": [
            "default",
            "internal",
            "authentication",
            "restricted",
            "allow_list",
            "priority_2",
        ],
        "Allow_Private_And_Local_Use_Addresses_To_Restricted_Internal_File_Sharing_Services": [
            "default",
            "internal",
            "file_sharing",
            "restricted",
            "allow_list",
            "priority_2",
        ],
        "Allow_Private_And_Local_Use_Addresses_To_Restricted_Database_Services": [
            "default",
            "internal",
            "database",
            "restricted",
            "sensitive",
            "allow_list",
            "priority_2",
        ],
        "Allow_Private_And_Local_Use_Addresses_To_Restricted_Monitoring_And_Logging_Services": [
            "default",
            "internal",
            "monitoring",
            "management",
            "restricted",
            "allow_list",
            "priority_2",
        ],
        "Deny_Invalid_Transit_Addresses_To_Any_TCP": [
            "default",
            "transit",
            "deny_list",
            "restricted",
            "priority_1",
        ],
        "Deny_Invalid_Transit_Addresses_To_Any_UDP": [
            "default",
            "transit",
            "deny_list",
            "restricted",
            "priority_1",
        ],
        "Deny_Documentation_And_Test_Addresses_To_Any_TCP": [
            "default",
            "documentation",
            "debugging",
            "deny_list",
            "priority_2",
        ],
        "Deny_Documentation_And_Test_Addresses_To_Any_UDP": [
            "default",
            "documentation",
            "debugging",
            "deny_list",
            "priority_2",
        ],
        "Deny_Multicast_Addresses_To_Any_TCP": [
            "default",
            "multicast",
            "deny_list",
            "restricted",
            "priority_2",
        ],
        "Deny_Multicast_Addresses_To_Any_UDP": [
            "default",
            "multicast",
            "deny_list",
            "restricted",
            "priority_2",
        ],
        "Deny_IPv6_Transition_And_Translation_Addresses_To_Any_TCP": [
            "default",
            "transit",
            "deny_list",
            "restricted",
            "priority_2",
        ],
        "Deny_IPv6_Transition_And_Translation_Addresses_To_Any_UDP": [
            "default",
            "transit",
            "deny_list",
            "restricted",
            "priority_2",
        ],
        "Deny_Private_And_Local_Use_Addresses_To_Deny_Legacy_Insecure_Services": [
            "default",
            "internal",
            "legacy",
            "deny_list",
            "restricted",
            "priority_3",
        ],
        "Deny_Private_And_Local_Use_Addresses_To_Deny_Tunneling_And_VPN_Services": [
            "default",
            "internal",
            "vpn",
            "deny_list",
            "restricted",
            "priority_3",
        ],
        "Deny_Private_And_Local_Use_Addresses_To_Deny_Voice_And_Signaling_Services": [
            "default",
            "internal",
            "voice",
            "deny_list",
            "restricted",
            "priority_3",
        ],
        "Deny_Private_And_Local_Use_Addresses_To_Deny_Local_Link_Resolution_Services": [
            "default",
            "internal",
            "link_local",
            "multicast",
            "deny_list",
            "restricted",
            "priority_3",
        ],
    }

    missing_tags = {
        tag_name for tag_names in rule_tag_mappings.values() for tag_name in tag_names if tag_name not in tags_by_name
    }
    if missing_tags:
        raise ValueError("Cannot tag default rules because these tags are missing: " + ", ".join(sorted(missing_tags)))

    missing_rules = [rule_name for rule_name in rule_tag_mappings if rule_name not in rules_by_name]
    if missing_rules:
        raise ValueError(
            "Cannot tag default rules because these rules are missing: " + ", ".join(sorted(missing_rules))
        )

    for rule_name, tag_names in rule_tag_mappings.items():
        rule = rules_by_name[rule_name]
        for tag_name in tag_names:
            add_tag_to_object(
                actor=actor,
                tenant_id=tenant_id,
                tag=tags_by_name[tag_name],
                obj=rule,
            )

    logger.info("Added tags to all seeded default rules.")


def add_tags_to_default_filters(
    actor: User,
    tenant_id: int,
    default_filters: list,
) -> None:
    """
    Add the correct tags to the seeded default filters.
    """
    require_write_tenant(actor, tenant_id)

    tenant_tags = get_all_tags_from_tenant(actor=actor, tenant_id=tenant_id)
    tags_by_name: dict[str, Tag] = {tag.name: tag for tag in tenant_tags}
    filters_by_name = {filter_obj.name: filter_obj for filter_obj in default_filters}

    filter_tag_mappings: dict[str, list[str]] = {
        "Baseline_Internal_Client_Policy": [
            "default",
            "internal",
            "allow_list",
            "deny_list",
            "restricted",
            "priority_1",
        ],
        "Internal_Server_Policy": [
            "default",
            "internal",
            "management",
            "authentication",
            "database",
            "file_sharing",
            "monitoring",
            "restricted",
            "priority_1",
        ],
        "Strict_Egress_Policy": [
            "default",
            "internal",
            "outbound",
            "deny_list",
            "allow_list",
            "restricted",
            "priority_1",
        ],
    }

    missing_tags = {
        tag_name for tag_names in filter_tag_mappings.values() for tag_name in tag_names if tag_name not in tags_by_name
    }
    if missing_tags:
        raise ValueError(
            "Cannot tag default filters because these tags are missing: " + ", ".join(sorted(missing_tags))
        )

    missing_filters = [filter_name for filter_name in filter_tag_mappings if filter_name not in filters_by_name]
    if missing_filters:
        raise ValueError(
            "Cannot tag default filters because these filters are missing: " + ", ".join(sorted(missing_filters))
        )

    for filter_name, tag_names in filter_tag_mappings.items():
        filter_obj = filters_by_name[filter_name]
        for tag_name in tag_names:
            add_tag_to_object(
                actor=actor,
                tenant_id=tenant_id,
                tag=tags_by_name[tag_name],
                obj=filter_obj,
            )

    logger.info("Added tags to all seeded default filters.")
