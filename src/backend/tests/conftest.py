import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.services.create import add_addresses_to_group, get_or_create_address
from backend.services.generate_config import PolicyRule
from backend.services.get import get_address_group_members, get_service_group_members
from constants import TESTING_TENNANT_ID


class MockRequest:
    session = {"current_tenant_id": TESTING_TENNANT_ID}


@pytest.fixture
def sample_addresses():
    sample_addresses = [
        Address(
            name="Test_Address_1",
            description="This is a test address for a standard IPv4 network",
            tenant_id=TESTING_TENNANT_ID,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="192.168.1.0/24",
        ),
        Address(
            name="Test_Address_2",
            description="This is a test address for any",
            tenant_id=TESTING_TENNANT_ID,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        ),
        Address(
            name="Test_Address_3",
            description="This tests a standard IPv6 address",
            tenant_id=TESTING_TENNANT_ID,
            addr_type="network",
            ipv6_type="standard",
            ipv6Network="ff00::/120",
        ),
        Address(
            name="Test_Address_4",
            description="This tests a custom range of IPv4 addresses",
            tenant_id=TESTING_TENNANT_ID,
            addr_type="range",
            ipv4_type="custom_range",
            ipv4Address_start="192.168.1.10",
            ipv4Address_end="192.168.1.20",
        ),
        Address(
            name="Test_Address_5",
            description="This tests a custom range of IPv6 addresses",
            tenant_id=TESTING_TENNANT_ID,
            addr_type="range",
            ipv6_type="custom_range",
            ipv6Address_start="ff00::10",
            ipv6Address_end="ff00::20",
        ),
    ]
    for address in sample_addresses:
        address.save()

    return sample_addresses


@pytest.fixture
def address_policy_rules(sample_addresses):
    policy_rules = []
    for i, address in enumerate(sample_addresses):
        rule = PolicyRule(
            name=f"Test_Address_Rule_{i + 1}",
            obj_type="address",
            action="accept" if i % 2 == 0 else "deny",
            object=address,
            direction="destination" if i % 2 == 0 else "source",
            sequence=i,
        )
        policy_rules.append(rule)

    return policy_rules

@pytest.fixture
def sample_services():
    services = [
        Service(
            name="Test_Service1",
            description="This tests a standard TCP service on port 80",
            tenant_id=TESTING_TENNANT_ID,
            protocol="tcp",
            port_start=80,
            port_end=80,
        ),
        Service(
            name="Test_Service2",
            description="This tests a standard UDP service on port 53",
            tenant_id=TESTING_TENNANT_ID,
            protocol="udp",
            port_start=53,
            port_end=53,
        ),
        Service(
            name="Test_Service3",
            description="This tests a custom range of TCP ports",
            tenant_id=TESTING_TENNANT_ID,
            protocol="tcp",
            port_start=1000,
            port_end=2000,
        ),
        Service(
            name="Test_Service4",
            description="This tests a custom range of UDP ports",
            tenant_id=TESTING_TENNANT_ID,
            protocol="udp",
            port_start=3000,
            port_end=4000,
        ),
        Service(
            name="Test_Service5",
            description="This tests a non-port-based protocol (ICMP)",
            tenant_id=TESTING_TENNANT_ID,
            protocol="icmp",
        ),
        Service(
            name="Test_Service6",
            description="This tests a non-port-based protocol (GRE)",
            tenant_id=TESTING_TENNANT_ID,
            protocol="gre",
        ),
    ]
    for service in services:
        service.save()
    return services


@pytest.fixture
def service_policy_rules(sample_services):
    policy_rules = []
    for i, service in enumerate(sample_services):
        rule = PolicyRule(
            name=f"Test_Service_Rule_{i + 1}",
            obj_type="service",
            action="accept" if i % 2 == 0 else "deny",
            object=service,
            direction="destination",
        )
        policy_rules.append(rule)

    return policy_rules


@pytest.fixture
def sample_address_group(sample_addresses):
    sample_address_group_1 = AddressGroup(
        name="Test_Address_Group_1",
        description="This is a test address group",
        tenant_id=TESTING_TENNANT_ID,
    )
    sample_address_group_1.save()

    add_addresses_to_group(
        address_group_id=sample_address_group_1.id,
        address_ids=[address.id for address in sample_addresses],
    )
    sample_address_group_1.save()

    sample_address_group_2 = AddressGroup(
        name="Test_Address_Group_2",
        description="This is another test address group",
        tenant_id=TESTING_TENNANT_ID,
    )
    sample_address_group_2.save()

    mock_request = MockRequest()
    sample_address_group_2_addresses = [
    get_or_create_address(
        request=mock_request,
        name="Private_Class_A_IPv4_RFC1918",
        description="RFC1918 private IPv4 Class A address space for internal networks.",
        ipv4_type="standard",
        ipv4Network="10.0.0.0/8",
    )[0],
    get_or_create_address(
        request=mock_request,
        name="Private_Class_B_IPv4_RFC1918",
        description="RFC1918 private IPv4 Class B address space for internal networks.",
        ipv4_type="standard",
        ipv4Network="172.16.0.0/12",
    )[0],
    get_or_create_address(
        request=mock_request,
        name="Private_Class_C_IPv4_RFC1918",
        description="RFC1918 private IPv4 Class C address space for internal networks.",
        ipv4_type="standard",
        ipv4Network="192.168.0.0/16",
    )[0],
    ]

    add_addresses_to_group(
        address_group_id=sample_address_group_2.id,
        address_ids=[address.id for address in sample_address_group_2_addresses],
    )
    sample_address_group_2.save()

    return sample_address_group_1, sample_address_group_2



@pytest.fixture
def address_group_policy_rules(sample_address_group):
    policy_rules = []

    rule = PolicyRule(
        name="Test_Rule_for_Address_Group_1",
        obj_type="address_group",
        action="accept",
        object=sample_address_group[0],
        direction="destination",
        sequence=0,
    )
    policy_rules.append(rule)
    rule = PolicyRule(
        name="Test_Rule_for_Address_Group_2",
        obj_type="address_group",
        action="deny",
        object=sample_address_group[1],
        direction="source",
        sequence=1,
    )
    policy_rules.append(rule)

    return policy_rules




