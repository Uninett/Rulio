import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.services.create import add_address_to_group
from backend.services.generate_config import PolicyRule, Policy
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
            ipv4_type="standard",
            ipv4Network="192.168.1.0/24",
        ),
        Address(
            name="Test_Address_2",
            description="This is a test address for any",
            tenant_id=TESTING_TENNANT_ID,
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        ),
        Address(
            name="Test_Address_3",
            description="This tests a standard IPv6 address",
            tenant_id=TESTING_TENNANT_ID,
            ipv6_type="standard",
            ipv6Network="ff00::/120",
        ),
        Address(
            name="Test_Address_4",
            description="This tests a custom range of IPv4 addresses",
            tenant_id=TESTING_TENNANT_ID,
            ipv4_type="custom_range",
            ipv4Address_start="192.168.1.10",
            ipv4Address_end="192.168.1.20",
        ),
        Address(
            name="Test_Address_5",
            description="This tests a custom range of IPv6 addresses",
            tenant_id=TESTING_TENNANT_ID,
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
            name=f"Test_Rule_{i + 1}",
            obj_type="address",
            action="accept" if i % 2 == 0 else "deny",
            object=address,
            direction="destination" if i % 2 == 0 else "source",
        )
        policy_rules.append(rule)

    return policy_rules


@pytest.fixture
def sample_address_group(sample_addresses):
    address_group = AddressGroup(
        name="Test_Address_Group",
        description="This is a test address group",
        tenant_id=TESTING_TENNANT_ID,
    )
    address_group.save()
    request = MockRequest()

    # for address in sample_addresses:
    #     add_address_to_group(request, address_group.id, address.id)

    return address_group


@pytest.fixture
def address_group_policy_rules(sample_address_group):
    policy_rules = []
    # for i, address in enumerate(sample_address_group.addresses):
    #     rule = PolicyRule(
    #         name=f"Test_Rule_{i + 1}",
    #         obj_type="address_group",
    #         action="accept" if i % 2 == 0 else "deny",
    #         object=sample_address_group,
    #         direction="destination" if i % 2 == 0 else "source",
    #     )
    #     policy_rules.append(rule)

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
    ]
    for service in services:
        service.save()
    return services


@pytest.fixture
def service_policy_rules(sample_services):
    policy_rules = []
    for i, service in enumerate(sample_services):
        rule = PolicyRule(
            name=f"Test_Rule_{i + 1}",
            obj_type="service",
            action="accept" if i % 2 == 0 else "deny",
            object=service,
            direction="destination",
        )
        policy_rules.append(rule)

    return policy_rules
