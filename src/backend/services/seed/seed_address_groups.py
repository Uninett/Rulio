from backend.services.attribute_objects.create_attribute_objects import get_or_create_address_group
from backend.services.get import get_all_addresses_from_tenant_by_names
from backend.utils.logger import set_up_logger
from constants import GLOBAL_TENANT_ID


logger = set_up_logger(__name__)


class MockRequest:
    session = {"current_tenant_id": GLOBAL_TENANT_ID}


def seed_addressgroups():
    mock_request = MockRequest()
    tenant_id = mock_request.session["current_tenant_id"]

    required_address_names = [
        "Private_Class_A_IPv4_RFC1918",
        "Private_Class_B_IPv4_RFC1918",
        "Private_Class_C_IPv4_RFC1918",
        "Loopback_IPv4_RFC1122",
        "LinkLocal_IPv4_RFC3927",
        "CGNAT_IPv4_RFC6598",
        "Benchmark_Testing_IPv4_RFC2544",
        "Unspecified_IPv4_RFC1122",
        "Limited_Broadcast_IPv4_RFC919_RFC922",
        "Reserved_IPv4_RFC1112_RFC6890",
        "Multicast_IPv4_RFC1112",
        "Local_Subnet_Multicast_IPv4_RFC1112",
        "TEST_NET_1_RFC5737",
        "TEST_NET_2_RFC5737",
        "TEST_NET_3_RFC5737",
        "ULA_IPv6_RFC4193",
        "ULA_Local_IPv6_RFC4193",
        "Loopback_IPv6_RFC4291",
        "LinkLocal_IPv6_RFC4291",
        "Unspecified_IPv6_RFC4291",
        "IPv4_Mapped_IPv6_RFC4291",
        "Multicast_IPv6_RFC4291",
        "All_Nodes_Multicast_IPv6_RFC4291",
        "All_Routers_Multicast_IPv6_RFC4291",
        "NAT64_Well_Known_Prefix_IPv6_RFC6052",
        "6to4_IPv6_RFC3056",
        "Teredo_IPv6_RFC4380",
    ]

    addresses = get_all_addresses_from_tenant_by_names(
        tenant_id=tenant_id,
        names=required_address_names,
    )
    address_ids_by_name = {address.name: address.id for address in addresses}

    missing_address_names = [name for name in required_address_names if name not in address_ids_by_name]
    if missing_address_names:
        raise ValueError(
            "Cannot seed address groups because these addresses are missing: " + ", ".join(missing_address_names)
        )

    default_address_groups = [
        # ---------------------------------------------------------------------
        # ACL - Private and Local Use Addresses
        # Commonly allowed on internal interfaces, but typically denied as
        # spoofed or non-public space on external/WAN interfaces.
        # ---------------------------------------------------------------------
        get_or_create_address_group(
            request=mock_request,
            name="Private_And_Local_Use_Addresses",
            description="Private, shared, unique-local, and link-local address ranges commonly used internally and typically denied on external interfaces.",
            members=[
                address_ids_by_name["Private_Class_A_IPv4_RFC1918"],
                address_ids_by_name["Private_Class_B_IPv4_RFC1918"],
                address_ids_by_name["Private_Class_C_IPv4_RFC1918"],
                address_ids_by_name["CGNAT_IPv4_RFC6598"],
                address_ids_by_name["LinkLocal_IPv4_RFC3927"],
                address_ids_by_name["ULA_IPv6_RFC4193"],
                address_ids_by_name["ULA_Local_IPv6_RFC4193"],
                address_ids_by_name["LinkLocal_IPv6_RFC4291"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Invalid Transit Addresses
        # Addresses that should generally never appear as normal routed transit
        # traffic and are commonly blocked in anti-spoofing and sanity ACLs.
        # ---------------------------------------------------------------------
        get_or_create_address_group(
            request=mock_request,
            name="Invalid_Transit_Addresses",
            description="Addresses that are generally invalid for normal routed transit traffic and are commonly blocked by anti-spoofing and sanity ACLs.",
            members=[
                address_ids_by_name["Unspecified_IPv4_RFC1122"],
                address_ids_by_name["Limited_Broadcast_IPv4_RFC919_RFC922"],
                address_ids_by_name["Loopback_IPv4_RFC1122"],
                address_ids_by_name["Reserved_IPv4_RFC1112_RFC6890"],
                address_ids_by_name["Unspecified_IPv6_RFC4291"],
                address_ids_by_name["Loopback_IPv6_RFC4291"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Documentation and Test Addresses
        # Reserved for examples, documentation, and benchmarking/lab use.
        # Usually blocked in production traffic flows.
        # ---------------------------------------------------------------------
        get_or_create_address_group(
            request=mock_request,
            name="Documentation_And_Test_Addresses",
            description="Addresses reserved for documentation, examples, and benchmarking or lab use, typically blocked in production traffic.",
            members=[
                address_ids_by_name["Benchmark_Testing_IPv4_RFC2544"],
                address_ids_by_name["TEST_NET_1_RFC5737"],
                address_ids_by_name["TEST_NET_2_RFC5737"],
                address_ids_by_name["TEST_NET_3_RFC5737"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - Multicast Addresses
        # Multicast ranges and well-known multicast destinations that are
        # usually blocked unless explicitly required for the environment.
        # ---------------------------------------------------------------------
        get_or_create_address_group(
            request=mock_request,
            name="Multicast_Addresses",
            description="IPv4 and IPv6 multicast ranges and well-known multicast destinations typically blocked unless explicitly required.",
            members=[
                address_ids_by_name["Multicast_IPv4_RFC1112"],
                address_ids_by_name["Local_Subnet_Multicast_IPv4_RFC1112"],
                address_ids_by_name["Multicast_IPv6_RFC4291"],
                address_ids_by_name["All_Nodes_Multicast_IPv6_RFC4291"],
                address_ids_by_name["All_Routers_Multicast_IPv6_RFC4291"],
            ],
        ),
        # ---------------------------------------------------------------------
        # ACL - IPv6 Transition and Translation Addresses
        # Prefixes associated with IPv6 transition and translation mechanisms.
        # Often explicitly allowed only when intentionally in use.
        # ---------------------------------------------------------------------
        get_or_create_address_group(
            request=mock_request,
            name="IPv6_Transition_And_Translation_Addresses",
            description="IPv6 prefixes used for transition and translation mechanisms, often explicitly blocked unless intentionally in use.",
            members=[
                address_ids_by_name["IPv4_Mapped_IPv6_RFC4291"],
                address_ids_by_name["NAT64_Well_Known_Prefix_IPv6_RFC6052"],
                address_ids_by_name["6to4_IPv6_RFC3056"],
                address_ids_by_name["Teredo_IPv6_RFC4380"],
            ],
        ),
    ]

    created_flags = [address_group[2] for address_group in default_address_groups]

    if all(created_flags):
        logger.info("All default address groups were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default address groups already existed. Missing address groups were created.")
    else:
        logger.warning("No default address groups were created because they already all existed.")

    return len(default_address_groups)
