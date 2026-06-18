from backend.services.create import get_or_create_address
from backend.utils.logger import set_up_logger
from constants import GLOBAL_TENNANT_ID


logger = set_up_logger(__name__)
class MockRequest:
    session = {"current_tenant_id": GLOBAL_TENNANT_ID}


def seed_addresses():
    mock_request = MockRequest()
    default_addresses = [
        # ---------------------------------------------------------------------
        # IPv4 - RFC1918 Private Networks
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Private_Class_A_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class A address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="10.0.0.0/8",
        ),
        get_or_create_address(
            request=mock_request,
            name="Private_Class_B_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class B address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="172.16.0.0/12",
        ),
        get_or_create_address(
            request=mock_request,
            name="Private_Class_C_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class C address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="192.168.0.0/16",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Special Use Addresses
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Loopback_IPv4_RFC1122",
            description="IPv4 loopback address space used for traffic sent to the local host itself, as defined by RFC1122.",
            ipv4_type="standard",
            ipv4Network="127.0.0.0/8",
        ),
        get_or_create_address(
            request=mock_request,
            name="LinkLocal_IPv4_RFC3927",
            description="IPv4 link-local address space used for automatic addressing on a local network segment when no DHCP server is available, as defined by RFC3927.",
            ipv4_type="standard",
            ipv4Network="169.254.0.0/16",
        ),
        get_or_create_address(
            request=mock_request,
            name="CGNAT_IPv4_RFC6598",
            description="Shared IPv4 address space reserved for Carrier-Grade NAT deployments by service providers, as defined by RFC6598.",
            ipv4_type="standard",
            ipv4Network="100.64.0.0/10",
        ),
        get_or_create_address(
            request=mock_request,
            name="Benchmark_Testing_IPv4_RFC2544",
            description="IPv4 address space reserved for network interconnect and benchmarking tests in lab environments, as defined by RFC2544.",
            ipv4_type="standard",
            ipv4Network="198.18.0.0/15",
        ),
        get_or_create_address(
            request=mock_request,
            name="Unspecified_IPv4_RFC1122",
            description="The IPv4 unspecified address used to indicate the absence of a specific source address, as described in RFC1122.",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/32",
        ),
        get_or_create_address(
            request=mock_request,
            name="Limited_Broadcast_IPv4_RFC919_RFC922",
            description="The IPv4 limited broadcast address used to reach all hosts on the local network segment, as described in RFC919 and RFC922.",
            ipv4_type="standard",
            ipv4Network="255.255.255.255/32",
        ),
        get_or_create_address(
            request=mock_request,
            name="Reserved_IPv4_RFC1112_RFC6890",
            description="IPv4 reserved address space set aside for future use, documented in RFC1112 and RFC6890.",
            ipv4_type="standard",
            ipv4Network="240.0.0.0/4",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Multicast
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Multicast_IPv4_RFC1112",
            description="IPv4 multicast address space used for one-to-many and many-to-many group communication, as defined by RFC1112.",
            ipv4_type="standard",
            ipv4Network="224.0.0.0/4",
        ),
        get_or_create_address(
            request=mock_request,
            name="Local_Subnet_Multicast_IPv4_RFC1112",
            description="IPv4 local subnet multicast control block used for protocol and control traffic on the local network segment, within the multicast space defined by RFC1112.",
            ipv4_type="standard",
            ipv4Network="224.0.0.0/24",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Documentation and Example Networks
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="TEST_NET_1_RFC5737",
            description="IPv4 documentation and example network TEST-NET-1 reserved for use in examples and documentation, as defined by RFC5737.",
            ipv4_type="standard",
            ipv4Network="192.0.2.0/24",
        ),
        get_or_create_address(
            request=mock_request,
            name="TEST_NET_2_RFC5737",
            description="IPv4 documentation and example network TEST-NET-2 reserved for use in examples and documentation, as defined by RFC5737.",
            ipv4_type="standard",
            ipv4Network="198.51.100.0/24",
        ),
        get_or_create_address(
            request=mock_request,
            name="TEST_NET_3_RFC5737",
            description="IPv4 documentation and example network TEST-NET-3 reserved for use in examples and documentation, as defined by RFC5737.",
            ipv4_type="standard",
            ipv4Network="203.0.113.0/24",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Catch-All
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Any_IPv4_RFC4632",
            description="Matches any IPv4 address using the default IPv4 route prefix, as defined by CIDR in RFC4632.",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Unique Local Addresses
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="ULA_IPv6_RFC4193",
            description="IPv6 unique local address space reserved for private internal use, as defined by RFC4193.",
            ipv6_type="standard",
            ipv6Network="fc00::/7",
        ),
        get_or_create_address(
            request=mock_request,
            name="ULA_Local_IPv6_RFC4193",
            description="IPv6 locally assigned unique local address space commonly used for internal networks, within RFC4193 unique local addressing.",
            ipv6_type="standard",
            ipv6Network="fd00::/8",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Special Use Addresses
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Loopback_IPv6_RFC4291",
            description="The IPv6 loopback address used for traffic sent to the local host itself, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="::1/128",
        ),
        get_or_create_address(
            request=mock_request,
            name="LinkLocal_IPv6_RFC4291",
            description="IPv6 link-local unicast address space used for communication on the local network segment, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="fe80::/10",
        ),
        get_or_create_address(
            request=mock_request,
            name="Unspecified_IPv6_RFC4291",
            description="The IPv6 unspecified address used to indicate the absence of a specific address, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="::/128",
        ),
        get_or_create_address(
            request=mock_request,
            name="IPv4_Mapped_IPv6_RFC4291",
            description="IPv6 address space used to represent IPv4 addresses in IPv6 notation, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="::ffff:0:0/96",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Multicast
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Multicast_IPv6_RFC4291",
            description="IPv6 multicast address space used for one-to-many and many-to-many group communication, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="ff00::/8",
        ),
        get_or_create_address(
            request=mock_request,
            name="All_Nodes_Multicast_IPv6_RFC4291",
            description="IPv6 all-nodes multicast address used to reach all IPv6 nodes on the local network segment, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="ff02::1/128",
        ),
        get_or_create_address(
            request=mock_request,
            name="All_Routers_Multicast_IPv6_RFC4291",
            description="IPv6 all-routers multicast address used to reach all IPv6 routers on the local network segment, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="ff02::2/128",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Transition and Translation Mechanisms
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="NAT64_Well_Known_Prefix_IPv6_RFC6052",
            description="IPv6 well-known prefix used for NAT64 translation between IPv6 and IPv4 networks, as defined by RFC6052.",
            ipv6_type="standard",
            ipv6Network="64:ff9b::/96",
        ),
        get_or_create_address(
            request=mock_request,
            name="6to4_IPv6_RFC3056",
            description="IPv6 6to4 transition prefix used for automatic tunneling of IPv6 over IPv4, as defined by RFC3056.",
            ipv6_type="standard",
            ipv6Network="2002::/16",
        ),
        get_or_create_address(
            request=mock_request,
            name="Teredo_IPv6_RFC4380",
            description="IPv6 Teredo transition prefix used for tunneling IPv6 connectivity across IPv4 NAT environments, as defined by RFC4380.",
            ipv6_type="standard",
            ipv6Network="2001::/32",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Documentation and Example Networks
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Documentation_IPv6_RFC3849",
            description="IPv6 documentation and example address space reserved for use in examples and documentation, as defined by RFC3849.",
            ipv6_type="standard",
            ipv6Network="2001:db8::/32",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Catch-All
        # ---------------------------------------------------------------------
        get_or_create_address(
            request=mock_request,
            name="Any_IPv6_RFC4291",
            description="Matches any IPv6 address using the default IPv6 route prefix, as defined by RFC4291.",
            ipv6_type="standard",
            ipv6Network="::/0",
        ),
    ]
    created_flags = [address[2] for address in default_addresses]
    if all(created_flags):
        logger.info("All default addresses were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default addresses already existed. Missing addresses were created.")
    else:
        logger.warning("No default addresses were created because they already all existed.")
    return len(default_addresses)
