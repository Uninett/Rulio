
from backend.services.create import create_address
from constants import GLOBAL_TENNANT_ID


class MockRequest:
    session = {"current_tenant_id": GLOBAL_TENNANT_ID}


def seed_addresses():
    mock_request = MockRequest()

    default_addresses = [
        # ---------------------------------------------------------------------
        # IPv4 - RFC1918 Private Networks
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Private_IPv4_10_8",
            description="RFC1918 private IPv4 address space for internal networks: 10.0.0.0/8.",
            ipv4_type="standard",
            ipv4Network="10.0.0.0/8",
        ),
        create_address(
            request=mock_request,
            name="Private_IPv4_172_16_12",
            description="RFC1918 private IPv4 address space for internal networks: 172.16.0.0/12.",
            ipv4_type="standard",
            ipv4Network="172.16.0.0/12",
        ),
        create_address(
            request=mock_request,
            name="Private_IPv4_192_168_16",
            description="RFC1918 private IPv4 address space for internal networks: 192.168.0.0/16.",
            ipv4_type="standard",
            ipv4Network="192.168.0.0/16",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Special Use Addresses
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Loopback_IPv4",
            description="IPv4 loopback address space used for traffic sent to the local host itself: 127.0.0.0/8.",
            ipv4_type="standard",
            ipv4Network="127.0.0.0/8",
        ),
        create_address(
            request=mock_request,
            name="LinkLocal_IPv4",
            description="IPv4 link-local address space used for automatic addressing on a local network segment when no DHCP server is available: 169.254.0.0/16.",
            ipv4_type="standard",
            ipv4Network="169.254.0.0/16",
        ),
        create_address(
            request=mock_request,
            name="CGNAT_IPv4",
            description="Shared IPv4 address space reserved for Carrier-Grade NAT deployments by service providers: 100.64.0.0/10.",
            ipv4_type="standard",
            ipv4Network="100.64.0.0/10",
        ),
        create_address(
            request=mock_request,
            name="Benchmark_Testing_IPv4",
            description="IPv4 address space reserved for network interconnect and benchmarking tests in lab environments: 198.18.0.0/15.",
            ipv4_type="standard",
            ipv4Network="198.18.0.0/15",
        ),
        create_address(
            request=mock_request,
            name="Unspecified_IPv4",
            description="The IPv4 unspecified address used to indicate the absence of a specific source address: 0.0.0.0/32.",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/32",
        ),
        create_address(
            request=mock_request,
            name="Limited_Broadcast_IPv4",
            description="The IPv4 limited broadcast address used to reach all hosts on the local network segment: 255.255.255.255/32.",
            ipv4_type="standard",
            ipv4Network="255.255.255.255/32",
        ),
        create_address(
            request=mock_request,
            name="Reserved_IPv4_240_4",
            description="IPv4 reserved address space set aside for future use: 240.0.0.0/4.",
            ipv4_type="standard",
            ipv4Network="240.0.0.0/4",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Multicast
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Multicast_IPv4",
            description="IPv4 multicast address space used for one-to-many and many-to-many group communication: 224.0.0.0/4.",
            ipv4_type="standard",
            ipv4Network="224.0.0.0/4",
        ),
        create_address(
            request=mock_request,
            name="Local_Subnet_Multicast_IPv4",
            description="IPv4 local subnet multicast control block used for protocol and control traffic on the local network segment: 224.0.0.0/24.",
            ipv4_type="standard",
            ipv4Network="224.0.0.0/24",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Documentation and Example Networks
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Documentation_IPv4_TEST_NET_1",
            description="IPv4 documentation and example network TEST-NET-1 reserved for use in examples and documentation: 192.0.2.0/24.",
            ipv4_type="standard",
            ipv4Network="192.0.2.0/24",
        ),
        create_address(
            request=mock_request,
            name="Documentation_IPv4_TEST_NET_2",
            description="IPv4 documentation and example network TEST-NET-2 reserved for use in examples and documentation: 198.51.100.0/24.",
            ipv4_type="standard",
            ipv4Network="198.51.100.0/24",
        ),
        create_address(
            request=mock_request,
            name="Documentation_IPv4_TEST_NET_3",
            description="IPv4 documentation and example network TEST-NET-3 reserved for use in examples and documentation: 203.0.113.0/24.",
            ipv4_type="standard",
            ipv4Network="203.0.113.0/24",
        ),

        # ---------------------------------------------------------------------
        # IPv4 - Catch-All
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Any_IPv4",
            description="Matches any IPv4 address: 0.0.0.0/0.",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Unique Local Addresses
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="ULA_IPv6",
            description="IPv6 unique local address space reserved for private internal use: fc00::/7.",
            ipv6_type="standard",
            ipv6Network="fc00::/7",
        ),
        create_address(
            request=mock_request,
            name="ULA_Local_IPv6",
            description="IPv6 locally assigned unique local address space commonly used for internal networks: fd00::/8.",
            ipv6_type="standard",
            ipv6Network="fd00::/8",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Special Use Addresses
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Loopback_IPv6",
            description="The IPv6 loopback address used for traffic sent to the local host itself: ::1/128.",
            ipv6_type="standard",
            ipv6Network="::1/128",
        ),
        create_address(
            request=mock_request,
            name="LinkLocal_IPv6",
            description="IPv6 link-local unicast address space used for communication on the local network segment: fe80::/10.",
            ipv6_type="standard",
            ipv6Network="fe80::/10",
        ),
        create_address(
            request=mock_request,
            name="Unspecified_IPv6",
            description="The IPv6 unspecified address used to indicate the absence of a specific address: ::/128.",
            ipv6_type="standard",
            ipv6Network="::/128",
        ),
        create_address(
            request=mock_request,
            name="IPv4_Mapped_IPv6",
            description="IPv6 address space used to represent IPv4 addresses in IPv6 notation: ::ffff:0:0/96.",
            ipv6_type="standard",
            ipv6Network="::ffff:0:0/96",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Multicast
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Multicast_IPv6",
            description="IPv6 multicast address space used for one-to-many and many-to-many group communication: ff00::/8.",
            ipv6_type="standard",
            ipv6Network="ff00::/8",
        ),
        create_address(
            request=mock_request,
            name="All_Nodes_Multicast_IPv6",
            description="IPv6 all-nodes multicast address used to reach all IPv6 nodes on the local network segment: ff02::1/128.",
            ipv6_type="standard",
            ipv6Network="ff02::1/128",
        ),
        create_address(
            request=mock_request,
            name="All_Routers_Multicast_IPv6",
            description="IPv6 all-routers multicast address used to reach all IPv6 routers on the local network segment: ff02::2/128.",
            ipv6_type="standard",
            ipv6Network="ff02::2/128",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Transition and Translation Mechanisms
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="NAT64_Well_Known_Prefix_IPv6",
            description="IPv6 well-known prefix used for NAT64 translation between IPv6 and IPv4 networks: 64:ff9b::/96.",
            ipv6_type="standard",
            ipv6Network="64:ff9b::/96",
        ),
        create_address(
            request=mock_request,
            name="SixToFour_IPv6",
            description="IPv6 6to4 transition prefix used for automatic tunneling of IPv6 over IPv4: 2002::/16.",
            ipv6_type="standard",
            ipv6Network="2002::/16",
        ),
        create_address(
            request=mock_request,
            name="Teredo_IPv6",
            description="IPv6 Teredo transition prefix used for tunneling IPv6 connectivity across IPv4 NAT environments: 2001::/32.",
            ipv6_type="standard",
            ipv6Network="2001::/32",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Documentation and Example Networks
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Documentation_IPv6",
            description="IPv6 documentation and example address space reserved for use in examples and documentation: 2001:db8::/32.",
            ipv6_type="standard",
            ipv6Network="2001:db8::/32",
        ),

        # ---------------------------------------------------------------------
        # IPv6 - Catch-All
        # ---------------------------------------------------------------------
        create_address(
            request=mock_request,
            name="Any_IPv6",
            description="Matches any IPv6 address: ::/0.",
            ipv6_type="standard",
            ipv6Network="::/0",
        ),
    ]

    return default_addresses