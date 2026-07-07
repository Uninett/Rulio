import pytest

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup

from backend.objects.tenant_objects.tenant import Tenant
from backend.services.membership import (
    add_addresses_to_group,
    add_devices_to_group,
    add_objects_to_rule,
    add_services_to_group,
)
from backend.services.attribute_objects.create_attribute_objects import create_tag, get_or_create_address
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule

from backend.services.config_generation.generate_config import PolicyRule, PolicyRuleMember
from backend.services.tenant_objects.create_tenant_objects import (
    create_device,
    get_or_create_device_group,
    get_or_create_interface,
)
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


class MockUser:
    def __init__(self, user_id):
        self.id = user_id


@pytest.fixture
def superuser(db):
    User = get_user_model()
    return User.objects.create_superuser(username="admin", password="change-me")


@pytest.fixture
def authenticated_client(superuser):
    client = Client()
    client.force_login(superuser)
    return client


@pytest.fixture
def get_testing_tenant_id():
    tenant, _ = Tenant.objects.get_or_create(tenant_name="Test Tenant")
    return tenant.id


@pytest.fixture
def authenticated_client_with_tenant(authenticated_client, create_testing_tenant):
    response = authenticated_client.get(f"/api/set_tenant?tenant_id={create_testing_tenant.id}")
    assert response.status_code == 200
    return authenticated_client


@pytest.fixture
def authenticated_user_and_tenant_id(authenticated_client, create_testing_tenant):
    response = authenticated_client.get(f"/api/set_tenant?tenant_id={create_testing_tenant.id}")
    user = User.objects.get(id=authenticated_client.session["_auth_user_id"])
    assert response.status_code == 200
    return user, create_testing_tenant.id


@pytest.fixture(scope="session")
def create_testing_tenant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        tenant, _ = Tenant.objects.get_or_create(
            tenant_name="Test Tenant",
        )
        return tenant


@pytest.fixture
def request_with_session(create_testing_tenant, authenticated_user_and_tenant_id):
    factory = RequestFactory()
    request = factory.get("/")
    request.session = {"current_tenant_id": create_testing_tenant.id}
    request.user, request.tenant_id = authenticated_user_and_tenant_id
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
def sample_address_group(sample_addresses, authenticated_client_with_tenant, request_with_session):
    sample_address_group_1 = AddressGroup(
        name="Test_Address_Group_1",
        description="This is a test address group",
        tenant_id=request_with_session.tenant_id,
    )
    sample_address_group_1.save()

    add_addresses_to_group(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        address_group_id=sample_address_group_1.id,
        address_ids=[address.id for address in sample_addresses],
    )
    sample_address_group_1.save()

    sample_address_group_2 = AddressGroup(
        name="Test_Address_Group_2",
        description="This is another test address group",
        tenant_id=request_with_session.tenant_id,
    )
    sample_address_group_2.save()

    sample_address_group_2_addresses = [
        get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Private_Class_A_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class A address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="10.0.0.0/8",
        )[0],
        get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Private_Class_B_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class B address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="172.16.0.0/12",
        )[0],
        get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Private_Class_C_IPv4_RFC1918",
            description="RFC1918 private IPv4 Class C address space for internal networks.",
            ipv4_type="standard",
            ipv4Network="192.168.0.0/16",
        )[0],
    ]

    add_addresses_to_group(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        address_group_id=sample_address_group_2.id,
        address_ids=[address.id for address in sample_address_group_2_addresses],
    )
    sample_address_group_2.save()

    return sample_address_group_1, sample_address_group_2


@pytest.fixture
def sample_service_group(sample_services, request_with_session):
    sample_service_group_1 = ServiceGroup(
        name="Test_Service_Group_1",
        description="This is a test service group",
        tenant_id=request_with_session.tenant_id,
    )
    sample_service_group_1.save()

    add_services_to_group(
        service_group_id=sample_service_group_1.id,
        service_ids=[service.id for service in sample_services],
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
    )
    sample_service_group_1.save()

    return sample_service_group_1




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
def realistic_acl_address_groups(realistic_acl_addresses, create_testing_tenant, request_with_session):
    by_name = {address.name: address for address in realistic_acl_addresses}

    trusted_sources = AddressGroup(
        name="ACL_Trusted_Sources",
        description="Trusted internal source subnets",
        tenant_id=create_testing_tenant.id,
    )
    trusted_sources.save()
    add_addresses_to_group(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
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
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        address_group_id=web_servers.id,
        address_ids=[
            by_name["ACL_Dst_Web_1"].id,
            by_name["ACL_Dst_Web_2"].id,
        ],
    )

    return [trusted_sources, web_servers]


@pytest.fixture
def realistic_acl_service_groups(realistic_acl_services, create_testing_tenant, request_with_session):
    by_name = {service.name: service for service in realistic_acl_services}

    web_services = ServiceGroup(
        name="ACL_Web_Services",
        description="Web services",
        tenant_id=create_testing_tenant.id,
    )
    web_services.save()
    add_services_to_group(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
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
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        service_group_id=dns_services.id,
        service_ids=[
            by_name["ACL_DNS_TCP"].id,
            by_name["ACL_DNS_UDP"].id,
        ],
    )

    return [web_services, dns_services]


@pytest.fixture
def sample_filters(request_with_session, create_testing_tenant):
    return [
        create_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Filter",
            description="This is a sample filter for testing.",
        ),
        create_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Filter_2",
            description="This is another sample filter for testing.",
        ),
    ]


@pytest.fixture
def sample_rules(request_with_session, sample_addresses, sample_services, create_testing_tenant, sample_filters):
    sample_rules = [
        create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Rule_1",
            filter=sample_filters[0],
            rule_sequence=1,
            enable=True,
            description="This is a sample rule for testing.",
            action="accept",
            log_type="all",
            hit_count=0,
        ),
        create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Rule_2",
            filter=sample_filters[0],
            rule_sequence=2,
            enable=True,
            description="This is another sample rule for testing.",
            action="deny",
            log_type="all",
            hit_count=0,
        ),
        create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Rule_3",
            filter=sample_filters[1],
            rule_sequence=1,
            enable=True,
            description="This is yet another sample rule for testing.",
            action="accept",
            log_type="all",
            hit_count=0,
        ),
        create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Rule_4",
            filter=sample_filters[1],
            rule_sequence=2,
            enable=True,
            description="This is a fourth sample rule for testing.",
            action="deny",
            log_type="all",
            hit_count=0,
        ),
    ]
    return sample_rules


@pytest.fixture
def sample_rules_with_objects(request_with_session, sample_rules, sample_addresses, sample_services):
    # Add objects to the rules
    add_objects_to_rule(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        rule_id=sample_rules[0].id,
        match_type="source",
        objects=[sample_addresses[0]],
    )
    add_objects_to_rule(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        rule_id=sample_rules[1].id,
        match_type="destination",
        objects=[sample_services[0]],
    )
    add_objects_to_rule(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        rule_id=sample_rules[2].id,
        match_type="source",
        objects=[sample_addresses[1]],
    )
    add_objects_to_rule(
        actor=request_with_session.user,
        tenant_id=request_with_session.tenant_id,
        rule_id=sample_rules[3].id,
        match_type="destination",
        objects=[sample_services[1]],
    )
    return sample_rules


@pytest.fixture
def sample_tags(request_with_session, create_testing_tenant):
    tags = [
        create_tag(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Tag_1",
            description="This is a sample tag for testing.",
        ),
        create_tag(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Tag_2",
            description="This is another sample tag for testing.",
        ),
    ]
    for tag in tags:
        tag.save()
    return tags


@pytest.fixture
def sample_devices(request_with_session, create_testing_tenant):
    devices = [
        create_device(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_1",
            description="This is a sample device for testing.",
            platform="juniper",
            type="firewall",
        ),
        create_device(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_2",
            description="This is another sample device for testing.",
            platform="cisco",
            type="router",
        ),
        create_device(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_3",
            description="This is yet another sample device for testing.",
            platform="arista",
            type="firewall",
        ),
        create_device(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_4",
            description="This is a fourth sample device for testing.",
            platform="fortinet",
            type="firewall",
        ),
    ]
    for device in devices:
        device.save()
    return devices


@pytest.fixture
def sample_device_groups(request_with_session, sample_devices, create_testing_tenant):
    device_groups = [
        get_or_create_device_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_Group_1",
            description="This is a sample device group for testing.",
        ),
        get_or_create_device_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_Group_2",
            description="This is another sample device group for testing.",
        ),
        get_or_create_device_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Sample_Device_Group_3",
            description="This is yet another sample device group for testing.",
        ),
    ]
    for i in range(len(device_groups)):
        if i % 3 == 0:
            add_devices_to_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                device_group_id=device_groups[i % 3].id,
                device_ids=[sample_devices[i].id],
            )

    return device_groups


@pytest.fixture
def sample_interfaces(request_with_session, sample_devices):
    interfaces = []
    for device in sample_devices:
        for i in range(1, 3):  # Create 2 interfaces per device
            interface, _, _, _, _, _ = get_or_create_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                device_id=device.id,
                name=f"ge-0/0/{i}",
                description=f"Sample interface {i} for {device.name}",
                type="physical",
            )
            interfaces.append(interface)
    return interfaces
