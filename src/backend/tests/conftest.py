import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.services.generate_config import PolicyRule, Policy


@pytest.fixture
def sample_addresses(self):
    sample_addresses = []
    sample_addresses.append(
        Address(
            name="Test_Address_1",
            description="This is a test address for a standard IPv4 network",
            tenant_id=42,
            ipv4_type="standard",
            ipv4Network="192.168.1.0/24",
        ),
        Address(
            name="Test_Address_2",
            description="This is a test address for any",
            tenant_id=42,
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
  
        ),
        Address(
            name="Test_Address_3",
            description="This tests a standard IPv6 address",
            tenant_id=42,
            ipv6_type="standard",
            ipv6Network="fw00::/120",
        ),
        Address(
            name="Test_Address_4",
            description="This tests a custom range of IPv4 addresses",
            tenant_id=42,
            ipv4_type="custom_range",
            ipv4Address_start="192.168.1.10",
            ipv4Address_end="192.168.1.20",
        ),
        
    )
    return sample_addresses


@pytest.fixture
def address_policy_rules(self, sample_addresses):
    policy_rules = []
    for i, address in enumerate(sample_addresses):
        rule = PolicyRule(
            name=f"Test_Rule_{i + 1}",
            obj_type="address",
            action="accept" if i % 2 == 0 else "deny",
            object=address,
            direction="destination" if i % 2 == 0 else "source",
        )
        policy_rules.append(rule)

    return policy_rules


@pytest.fixture
def sample_address_group(self, sample_addresses):
    address_group = AddressGroup(
        name="Test_Address_Group",
        description="This is a test address group",
        tenant_id=42,
    )

    for address in sample_addresses:
        address_group.add_address_to_group(address)

    return address_group


@pytest.fixture
def address_group_policy_rules(self, sample_address_group):
    pass


@pytest.fixture
def sample_services(self):
    service1 = Service(
        name="Test_Service1",
        description="This is a test service",
        tenant_id=42,
        protocol="tcp",
        port_start=80,
        port_end=80,
    )

    service2 = Service(
        name="Test_Service2",
        description="This is another test service",
        tenant_id=42,
        protocol="udp",
        port_start=53,
        port_end=53,
    )

    return service1, service2


@pytest.fixture
def service_policy_rules(self, sample_services):
    service1, service2 = sample_services

    PolicyRule1 = PolicyRule(
        name="Test_Rule_1",
        obj_type="service",
        action="accept",
        object=service1,
        direction="destination",
    )

    PolicyRule2 = PolicyRule(
        name="Test_Rule_2",
        obj_type="service",
        action="deny",
        object=service2,
        direction="destination",
    )
    return [PolicyRule1, PolicyRule2]
