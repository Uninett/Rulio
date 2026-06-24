import pytest

from django.test import RequestFactory

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.management.tenant import Tenant
from backend.services.create import (
    add_addresses_to_group,
    add_services_to_group,
    create_filter,
    create_rule,
    get_or_create_address,
)
from backend.services.generate_config import PolicyRule
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


class MockUser:
    def __init__(self, user_id):
        self.id = user_id


@pytest.fixture(scope="session")
def create_testing_tenant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        tenant, created = Tenant.objects.get_or_create(
            tenant_name="Test Tenant",
        )
        return tenant


@pytest.fixture
def request_with_session(create_testing_tenant):
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {"current_tenant_id": create_testing_tenant.id}
    request.tenant = create_testing_tenant
    request.user = MockUser(user_id=2)  # Mock user for testing purposes
    return request


@pytest.fixture
def sample_addresses(create_testing_tenant):
    sample_addresses = [
        Address(
            name="Test_Address_1",
            description="This is a test address for a standard IPv4 network",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="192.168.1.0/24",
        ),
        Address(
            name="Test_Address_2",
            description="This is a test address for any",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        ),
        Address(
            name="Test_Address_3",
            description="This tests a standard IPv6 address",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv6_type="standard",
            ipv6Network="ff00::/120",
        ),
        Address(
            name="Test_Address_4",
            description="This tests a custom range of IPv4 addresses",
            tenant_id=create_testing_tenant.id,
            addr_type="range",
            ipv4_type="custom_range",
            ipv4Address_start="192.168.1.10",
            ipv4Address_end="192.168.1.20",
        ),
        Address(
            name="Test_Address_5",
            description="This tests a custom range of IPv6 addresses",
            tenant_id=create_testing_tenant.id,
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
def sample_services(create_testing_tenant):
    services = [
        Service(
            name="Test_Service1",
            description="This tests a standard TCP service on port 80",
            tenant_id=create_testing_tenant.id,
            protocol="tcp",
            port_start=80,
            port_end=80,
        ),
        Service(
            name="Test_Service2",
            description="This tests a standard UDP service on port 53",
            tenant_id=create_testing_tenant.id,
            protocol="udp",
            port_start=53,
            port_end=53,
        ),
        Service(
            name="Test_Service3",
            description="This tests a custom range of TCP ports",
            tenant_id=create_testing_tenant.id,
            protocol="tcp",
            port_start=1000,
            port_end=2000,
        ),
        Service(
            name="Test_Service4",
            description="This tests a custom range of UDP ports",
            tenant_id=create_testing_tenant.id,
            protocol="udp",
            port_start=3000,
            port_end=4000,
        ),
        Service(
            name="Test_Service5",
            description="This tests a non-port-based protocol (ICMP)",
            tenant_id=create_testing_tenant.id,
            protocol="icmp",
        ),
        Service(
            name="Test_Service6",
            description="This tests a non-port-based protocol (GRE)",
            tenant_id=create_testing_tenant.id,
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
            sequence=i,
        )
        policy_rules.append(rule)

    return policy_rules


@pytest.fixture
def sample_address_group(sample_addresses, request_with_session, create_testing_tenant):
    sample_address_group_1 = AddressGroup(
        name="Test_Address_Group_1",
        description="This is a test address group",
        tenant_id=create_testing_tenant.id,
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
        tenant_id=create_testing_tenant.id,
    )
    sample_address_group_2.save()

    sample_address_group_2_addresses = [
        get_or_create_address(
            request=request_with_session,
            name="Private_Class_A_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class A address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="10.0.0.0/8",
        )[0],
        get_or_create_address(
            request=request_with_session,
            name="Private_Class_B_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class B address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="172.16.0.0/12",
        )[0],
        get_or_create_address(
            request=request_with_session,
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
def sample_service_group(sample_services, create_testing_tenant):
    sample_service_group_1 = ServiceGroup(
        name="Test_Service_Group_1",
        description="This is a test service group",
        tenant_id=create_testing_tenant.id,
    )
    sample_service_group_1.save()

    add_services_to_group(
        service_group_id=sample_service_group_1.id,
        service_ids=[service.id for service in sample_services],
    )
    sample_service_group_1.save()

    return sample_service_group_1


@pytest.fixture
def address_group_policy_rules(sample_address_group):
    return [
        PolicyRule(
            name="Test_Rule_for_Address_Group_1",
            obj_type="address_group",
            action="accept",
            object=sample_address_group[0],
            direction="destination",
            sequence=0,
        ),
        PolicyRule(
            name="Test_Rule_for_Address_Group_2",
            obj_type="address_group",
            action="deny",
            object=sample_address_group[1],
            direction="source",
            sequence=1,
        ),
    ]


@pytest.fixture
def service_group_policy_rules(sample_service_group):
    return [
        PolicyRule(
            name="Test_Rule_for_Service_Group_1",
            obj_type="service_group",
            action="accept",
            object=sample_service_group,
            direction="destination",
            sequence=0,
        )
    ]


@pytest.fixture
def combined_policy_rules(sample_addresses, sample_services):
    return [
        PolicyRule(
            name="Combined_Rule_1_Address",
            obj_type="address",
            action="accept",
            object=sample_addresses[0],
            direction="destination",
            sequence=0,
        ),
        PolicyRule(
            name="Combined_Rule_1_Service",
            obj_type="service",
            action="accept",
            object=sample_services[0],
            direction="destination",
            sequence=0,
        ),
        PolicyRule(
            name="Combined_Rule_2_Address",
            obj_type="address",
            action="deny",
            object=sample_addresses[1],
            direction="source",
            sequence=1,
        ),
        PolicyRule(
            name="Combined_Rule_2_Service",
            obj_type="service",
            action="deny",
            object=sample_services[1],
            direction="destination",
            sequence=1,
        ),
    ]


@pytest.fixture
def realistic_acl_addresses(create_testing_tenant):
    addresses = [
        Address(
            name="ACL_Src_Users",
            description="Internal user subnet",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.10.10.0/24",
        ),
        Address(
            name="ACL_Src_Admins",
            description="Admin subnet",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.20.20.0/24",
        ),
        Address(
            name="ACL_Dst_Web_1",
            description="Primary web server",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="172.16.10.10/32",
        ),
        Address(
            name="ACL_Dst_Web_2",
            description="Secondary web server",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="172.16.10.11/32",
        ),
        Address(
            name="ACL_Dst_DNS",
            description="DNS server",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="172.16.20.53/32",
        ),
        Address(
            name="ACL_Dst_Blocked",
            description="Blocked external host",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="203.0.113.66/32",
        ),
        Address(
            name="ACL_Any",
            description="Any IPv4 destination",
            tenant_id=create_testing_tenant.id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        ),
    ]

    for address in addresses:
        address.save()

    return addresses


@pytest.fixture
def realistic_acl_services(create_testing_tenant):
    services = [
        Service(
            name="ACL_HTTP",
            description="HTTP",
            tenant_id=create_testing_tenant.id,
            protocol="tcp",
            port_start=80,
            port_end=80,
        ),
        Service(
            name="ACL_HTTPS",
            description="HTTPS",
            tenant_id=create_testing_tenant.id,
            protocol="tcp",
            port_start=443,
            port_end=443,
        ),
        Service(
            name="ACL_DNS_TCP",
            description="DNS over TCP",
            tenant_id=create_testing_tenant.id,
            protocol="tcp",
            port_start=53,
            port_end=53,
        ),
        Service(
            name="ACL_DNS_UDP",
            description="DNS over UDP",
            tenant_id=create_testing_tenant.id,
            protocol="udp",
            port_start=53,
            port_end=53,
        ),
        Service(
            name="ACL_ICMP",
            description="ICMP",
            tenant_id=create_testing_tenant.id,
            protocol="icmp",
        ),
    ]

    for service in services:
        service.save()

    return services


@pytest.fixture
def realistic_acl_address_groups(realistic_acl_addresses, create_testing_tenant):
    by_name = {address.name: address for address in realistic_acl_addresses}

    trusted_sources = AddressGroup(
        name="ACL_Trusted_Sources",
        description="Trusted internal source subnets",
        tenant_id=create_testing_tenant.id,
    )
    trusted_sources.save()
    add_addresses_to_group(
        address_group_id=trusted_sources.id,
        address_ids=[
            by_name["ACL_Src_Users"].id,
            by_name["ACL_Src_Admins"].id,
        ],
    )

    web_servers = AddressGroup(
        name="ACL_Web_Servers",
        description="Web server farm",
        tenant_id=create_testing_tenant.id,
    )
    web_servers.save()
    add_addresses_to_group(
        address_group_id=web_servers.id,
        address_ids=[
            by_name["ACL_Dst_Web_1"].id,
            by_name["ACL_Dst_Web_2"].id,
        ],
    )

    return {
        "trusted_sources": trusted_sources,
        "web_servers": web_servers,
    }


@pytest.fixture
def realistic_acl_service_groups(realistic_acl_services, create_testing_tenant):
    by_name = {service.name: service for service in realistic_acl_services}

    web_services = ServiceGroup(
        name="ACL_Web_Services",
        description="Web services",
        tenant_id=create_testing_tenant.id,
    )
    web_services.save()
    add_services_to_group(
        service_group_id=web_services.id,
        service_ids=[
            by_name["ACL_HTTP"].id,
            by_name["ACL_HTTPS"].id,
        ],
    )

    dns_services = ServiceGroup(
        name="ACL_DNS_Services",
        description="DNS services",
        tenant_id=create_testing_tenant.id,
    )
    dns_services.save()
    add_services_to_group(
        service_group_id=dns_services.id,
        service_ids=[
            by_name["ACL_DNS_TCP"].id,
            by_name["ACL_DNS_UDP"].id,
        ],
    )

    return {
        "web_services": web_services,
        "dns_services": dns_services,
    }


@pytest.fixture
def realistic_acl_policy_rules(
    realistic_acl_addresses,
    realistic_acl_services,
    realistic_acl_address_groups,
    realistic_acl_service_groups,
):
    addr = {a.name: a for a in realistic_acl_addresses}
    svc = {s.name: s for s in realistic_acl_services}
    ag = realistic_acl_address_groups
    sg = realistic_acl_service_groups

    return [
        # Sequence 10 -> 1 tcp term
        PolicyRule(
            name="Allow_Trusted_To_Web_Src_Group",
            obj_type="address_group",
            action="accept",
            object=ag["trusted_sources"],
            direction="source",
            sequence=10,
        ),
        PolicyRule(
            name="Allow_Trusted_To_Web_Dst_Group",
            obj_type="address_group",
            action="accept",
            object=ag["web_servers"],
            direction="destination",
            sequence=10,
        ),
        PolicyRule(
            name="Allow_Trusted_To_Web_Dst_Direct",
            obj_type="address",
            action="accept",
            object=addr["ACL_Dst_Web_1"],
            direction="destination",
            sequence=10,
        ),
        PolicyRule(
            name="Allow_Trusted_To_Web_Services",
            obj_type="service_group",
            action="accept",
            object=sg["web_services"],
            direction="destination",
            sequence=10,
        ),
        # Sequence 20 -> 2 terms (tcp + udp)
        PolicyRule(
            name="Allow_Trusted_To_DNS_Src_Group",
            obj_type="address_group",
            action="accept",
            object=ag["trusted_sources"],
            direction="source",
            sequence=20,
        ),
        PolicyRule(
            name="Allow_Trusted_To_DNS_Dst",
            obj_type="address",
            action="accept",
            object=addr["ACL_Dst_DNS"],
            direction="destination",
            sequence=20,
        ),
        PolicyRule(
            name="Allow_Trusted_To_DNS_Services",
            obj_type="service_group",
            action="accept",
            object=sg["dns_services"],
            direction="destination",
            sequence=20,
        ),
        # Sequence 30 -> 1 tcp term
        PolicyRule(
            name="Deny_Admins_To_Blocked_Src",
            obj_type="address",
            action="deny",
            object=addr["ACL_Src_Admins"],
            direction="source",
            sequence=30,
        ),
        PolicyRule(
            name="Deny_Admins_To_Blocked_Dst",
            obj_type="address",
            action="deny",
            object=addr["ACL_Dst_Blocked"],
            direction="destination",
            sequence=30,
        ),
        PolicyRule(
            name="Deny_Admins_To_Blocked_Service",
            obj_type="service",
            action="deny",
            object=svc["ACL_HTTPS"],
            direction="destination",
            sequence=30,
        ),
        # Sequence 40 -> 1 icmp term
        PolicyRule(
            name="Allow_Admins_ICMP_Src",
            obj_type="address",
            action="accept",
            object=addr["ACL_Src_Admins"],
            direction="source",
            sequence=40,
        ),
        PolicyRule(
            name="Allow_Admins_ICMP_Dst",
            obj_type="address",
            action="accept",
            object=addr["ACL_Any"],
            direction="destination",
            sequence=40,
        ),
        PolicyRule(
            name="Allow_Admins_ICMP_Service",
            obj_type="service",
            action="accept",
            object=svc["ACL_ICMP"],
            direction="destination",
            sequence=40,
        ),
    ]


@pytest.fixture
def sample_filter(request_with_session, create_testing_tenant):
    return create_filter(
        request=request_with_session,
        name="Sample Filter",
        description="This is a sample filter for testing.",
        enable=True,
    )


@pytest.fixture
def sample_rule(request_with_session, create_testing_tenant):
    return create_rule(
        request=request_with_session,
        name="Sample Rule",
        description="This is a sample rule for testing.",
        action="accept",
        log_type="all",
        hit_count=0,
        direction="source",
        enable=True,
    )
