import pytest
from django.core.exceptions import PermissionDenied

from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.filters.rule_match import RuleMatch
from backend.services.attribute_objects.create_attribute_objects import (
    create_address_group,
    create_service,
    create_service_group,
    get_or_create_address,
    get_or_create_address_group,
)
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.membership import (
    add_addresses_to_group,
    add_objects_to_rule,
    add_services_to_group,
)
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


@pytest.mark.django_db
class TestCreateAddress:
    def test_create_address(self, request_with_session, create_testing_tenant):

        address = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Address",
            description="This is a test address",
            addr_type="host",
            ipv4_type="standard",
            ipv6_type="standard",
            ipv4Network="192.168.1.1",
            ipv6Network="2001:db8::1",
        )[0]
        assert address is not None
        assert address.name == "Test Address"
        assert address.description == "This is a test address"
        assert address.tenant_id == request_with_session.tenant_id
        assert address.get_address()[0][0].__str__() == "192.168.1.1/32"
        assert address.get_address()[1][0].__str__() == "2001:db8::1/128"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type == "standard"

    def test_create_address_with_custom_range(self, request_with_session, create_testing_tenant):
        address = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Address Range",
            description="This is a test address range",
            addr_type="range",
            ipv4_type="custom_range",
            ipv6_type="custom_range",
            ipv4Address_start="192.168.1.1",
            ipv4Address_end="192.168.1.255",
            ipv6Address_start="2001:db8::1",
            ipv6Address_end="2001:db8::ffff",
        )[0]
        assert address is not None
        assert address.name == "Test Address Range"
        assert address.description == "This is a test address range"
        assert address.tenant_id == request_with_session.tenant_id
        print("custom range: ", address.get_address())
        ipv4_networks, ipv6_networks = address.get_address()

        assert str(ipv4_networks[0]) == "192.168.1.1/32"
        assert str(ipv4_networks[-1]) == "192.168.1.128/25"

        assert str(ipv6_networks[0]) == "2001:db8::1/128"
        assert str(ipv6_networks[-1]) == "2001:db8::8000/113"
        assert address.ipv4_type == "custom_range"
        assert address.ipv6_type == "custom_range"

    def test_get_or_create_address_with_ipv4_auto_host(self, request_with_session, create_testing_tenant):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto IPv4 Host",
            description="Auto detected IPv4 host",
            ipv4_auto="192.168.10.5",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "host"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type is None
        assert str(address.get_address()[0][0]) == "192.168.10.5/32"

    def test_get_or_create_address_with_ipv4_auto_network(self, request_with_session, create_testing_tenant):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto IPv4 Network",
            description="Auto detected IPv4 network",
            ipv4_auto="192.168.20.0/24",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "network"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type is None
        assert str(address.get_address()[0][0]) == "192.168.20.0/24"

    def test_get_or_create_address_with_ipv4_auto_range(self, request_with_session, create_testing_tenant):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto IPv4 Range",
            description="Auto detected IPv4 range",
            ipv4_auto="192.168.30.10-192.168.30.20",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "range"
        assert address.ipv4_type == "custom_range"
        assert address.ipv6_type is None

        ipv4_networks, _ = address.get_address()
        assert str(ipv4_networks[0]) == "192.168.30.10/31"
        assert str(ipv4_networks[-1]) == "192.168.30.20/32"

    def test_get_or_create_address_with_ipv6_auto_host(self, request_with_session, create_testing_tenant):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto IPv6 Host",
            description="Auto detected IPv6 host",
            ipv6_auto="2001:db8::10",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "host"
        assert address.ipv4_type is None
        assert address.ipv6_type == "standard"
        assert str(address.get_address()[1][0]) == "2001:db8::10/128"

    def test_get_or_create_address_with_ipv6_auto_network(self, request_with_session, create_testing_tenant):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto IPv6 Network",
            description="Auto detected IPv6 network",
            ipv6_auto="2001:db8:20::/64",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "network"
        assert address.ipv4_type is None
        assert address.ipv6_type == "standard"
        assert str(address.get_address()[1][0]) == "2001:db8:20::/64"

    def test_get_or_create_address_with_ipv6_auto_range(self, request_with_session, create_testing_tenant):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto IPv6 Range",
            description="Auto detected IPv6 range",
            ipv6_auto="2001:db8:30::10-2001:db8:30::20",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "range"
        assert address.ipv4_type is None
        assert address.ipv6_type == "custom_range"

        _, ipv6_networks = address.get_address()
        assert str(ipv6_networks[0]) == "2001:db8:30::10/124"
        assert str(ipv6_networks[-1]) == "2001:db8:30::20/128"

    def test_get_or_create_address_with_matching_ipv4_ipv6_auto_range(
        self, request_with_session, create_testing_tenant
    ):
        address, _, created = get_or_create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Auto Dual Stack Range",
            description="Auto detected dual stack range",
            ipv4_auto="192.168.60.10-192.168.60.20",
            ipv6_auto="2001:db8:60::10-2001:db8:60::20",
        )

        assert created is True
        assert address is not None
        assert address.addr_type == "range"
        assert address.ipv4_type == "custom_range"
        assert address.ipv6_type == "custom_range"

        ipv4_networks, ipv6_networks = address.get_address()
        assert str(ipv4_networks[0]) == "192.168.60.10/31"
        assert str(ipv4_networks[-1]) == "192.168.60.20/32"
        assert str(ipv6_networks[0]) == "2001:db8:60::10/124"
        assert str(ipv6_networks[-1]) == "2001:db8:60::20/128"

    def test_get_or_create_address_rejects_mixed_ipv4_host_and_ipv6_range(
        self, request_with_session, create_testing_tenant
    ):
        with pytest.raises(TypeError, match="Address type mismatch"):
            get_or_create_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name="Mixed Host Range",
                description="Should fail",
                ipv4_auto="192.168.70.10",
                ipv6_auto="2001:db8:70::10-2001:db8:70::20",
            )

    def test_get_or_create_address_rejects_mixed_ipv4_range_and_ipv6_host(
        self, request_with_session, create_testing_tenant
    ):
        with pytest.raises(TypeError, match="Address type mismatch"):
            get_or_create_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name="Mixed Range Host",
                description="Should fail",
                ipv4_auto="192.168.80.10-192.168.80.20",
                ipv6_auto="2001:db8::80",
            )

    def test_get_or_create_address_rejects_invalid_ipv4_range_with_cidr(
        self, request_with_session, create_testing_tenant
    ):
        with pytest.raises(ValueError, match="Invalid IPv4 range format"):
            get_or_create_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name="Invalid IPv4 Range",
                description="Should fail",
                ipv4_auto="192.168.90.0/24-192.168.90.20",
            )

    def test_get_or_create_address_rejects_invalid_ipv6_range_with_cidr(
        self, request_with_session, create_testing_tenant
    ):
        with pytest.raises(ValueError, match="Invalid IPv6 range format"):
            get_or_create_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name="Invalid IPv6 Range",
                description="Should fail",
                ipv6_auto="2001:db8:90::/64-2001:db8:90::20",
            )

    def test_get_or_create_address_rejects_mixed_ipv4_host_and_ipv6_network(
        self, request_with_session, create_testing_tenant
    ):
        with pytest.raises(TypeError, match="Address type mismatch"):
            get_or_create_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name="Mixed Host Network",
                description="Should fail",
                ipv4_auto="192.168.100.10",
                ipv6_auto="2001:db8:100::/64",
            )

    def test_get_or_create_address_rejects_mixed_ipv4_network_and_ipv6_host(
        self, request_with_session, create_testing_tenant
    ):
        with pytest.raises(TypeError, match="Address type mismatch"):
            get_or_create_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name="Mixed Network Host",
                description="Should fail",
                ipv4_auto="192.168.110.0/24",
                ipv6_auto="2001:db8::110",
            )

@pytest.mark.django_db
class TestCreateService:
    def test_create_service(self, request_with_session, create_testing_tenant):

        service = create_service(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Service",
            description="This is a test service",
            protocol="TCP",
            port_start=80,
            port_end=80,
        )
        assert service is not None
        assert service.name == "Test Service"
        assert service.description == "This is a test service"
        assert service.tenant_id == request_with_session.tenant_id
        assert service.protocol == "TCP"
        assert service.port_start == 80
        assert service.port_end == 80


@pytest.mark.django_db
class TestCreateAddressGroup:
    def test_create_address_group(self, request_with_session, create_testing_tenant):
        address_group = create_address_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Address Group",
            description="This is a test address group",
        )
        assert address_group is not None
        assert address_group.name == "Test Address Group"
        assert address_group.description == "This is a test address group"
        assert address_group.tenant_id == create_testing_tenant.id


@pytest.mark.django_db
class TestCreateServiceGroup:
    def test_create_service_group(self, request_with_session, create_testing_tenant):
        service_group = create_service_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Service Group",
            description="This is a test service group",
        )
        assert service_group is not None
        assert service_group.name == "Test Service Group"
        assert service_group.description == "This is a test service group"
        assert service_group.tenant_id == request_with_session.tenant_id

    def test_get_or_create_address_group_with_seeding_adds_members(self, sample_addresses, request_with_session):
        address_ids = [address.id for address in sample_addresses]

        address_group, _, created = get_or_create_address_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Seeded Address Group",
            description="Address group created during seeding",
            members=address_ids,
            request_type="seeding",
        )

        assert created is True
        assert AddressGroupMember.objects.filter(group=address_group).count() == len(address_ids)


@pytest.mark.django_db
class TestAddAddressToGroup:
    def test_add_address_to_group(self, sample_addresses, request_with_session):
        sample_address_ids = [address.id for address in sample_addresses]
        address_group = create_address_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Address Group",
            description="This is a test address group",
        )
        response = add_addresses_to_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            address_group_id=address_group.id,
            address_ids=sample_address_ids,
        )
        address_ids = [address.id for address in sample_addresses]

        assert response["address_group_id"] == address_group.id
        assert set(response["added_address_ids"]) == set(address_ids)
        assert response["not_found_address_ids"] == []
        assert response["already_present_address_ids"] == []

        for address_id in address_ids:
            assert AddressGroupMember.objects.filter(
                group_id=address_group.id,
                address_id=address_id,
            ).exists()


@pytest.mark.django_db
class TestAddAddressesToGroup:
    def test_add_addresses_to_group(self, sample_addresses, request_with_session):
        address_group = create_address_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Address Group",
            description="This is a test address group",
        )
        sample_address_ids = [address.id for address in sample_addresses]
        count_sample_addresses = len(sample_address_ids)
        mid = count_sample_addresses // 2
        sample_address_ids_batch_1 = sample_address_ids[:mid]

        response1 = add_addresses_to_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            address_group_id=address_group.id,
            address_ids=sample_address_ids_batch_1,
        )

        assert response1["address_group_id"] == address_group.id
        assert response1["added_address_ids"] == sample_address_ids_batch_1
        assert response1["not_found_address_ids"] == []
        assert response1["already_present_address_ids"] == []

        for address_id in sample_address_ids_batch_1:
            assert AddressGroupMember.objects.filter(
                group_id=address_group.id,
                address_id=address_id,
            ).exists()

        response2 = add_addresses_to_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            address_group_id=address_group.id,
            address_ids=sample_address_ids,
        )

        assert response2["address_group_id"] == address_group.id
        assert response2["added_address_ids"] == sample_address_ids[mid:]
        assert set(response2["already_present_address_ids"]) == set(sample_address_ids_batch_1)
        assert response2["not_found_address_ids"] == []

        for address_id in sample_address_ids:
            assert AddressGroupMember.objects.filter(
                group=address_group,
                address_id=address_id,
            ).exists()

        with pytest.raises(PermissionDenied):
            add_addresses_to_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                address_group_id=address_group.id,
                address_ids=[9999],
            )


@pytest.mark.django_db
class TestAddServiceToGroup:
    def test_add_service_to_group(self, sample_services, request_with_session):
        sample_service_ids = [service.id for service in sample_services]
        service_group = create_service_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Service Group",
            description="This is a test service group",
        )
        response = add_services_to_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            service_group_id=service_group.id,
            service_ids=sample_service_ids,
        )
        service_ids = [service.id for service in sample_services]

        assert response["service_group_id"] == service_group.id
        assert set(response["added_service_ids"]) == set(service_ids)
        assert response["not_found_service_ids"] == []
        assert response["already_present_service_ids"] == []

        for service_id in service_ids:
            assert ServiceGroupMember.objects.filter(
                group_id=service_group.id,
                service_id=service_id,
            ).exists()


@pytest.mark.django_db
class TestAddServicesToGroup:
    def test_add_services_to_group(self, sample_services, request_with_session):
        service_group = create_service_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Service Group",
            description="This is a test service group",
        )
        sample_service_ids = [service.id for service in sample_services]
        count_sample_services = len(sample_service_ids)
        mid = count_sample_services // 2
        sample_service_ids_batch_1 = sample_service_ids[:mid]

        response1 = add_services_to_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            service_group_id=service_group.id,
            service_ids=sample_service_ids_batch_1,
        )

        assert response1["service_group_id"] == service_group.id
        assert response1["added_service_ids"] == sample_service_ids_batch_1
        assert response1["not_found_service_ids"] == []
        assert response1["already_present_service_ids"] == []

        for service_id in sample_service_ids_batch_1:
            assert ServiceGroupMember.objects.filter(
                group_id=service_group.id,
                service_id=service_id,
            ).exists()

        response2 = add_services_to_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            service_group_id=service_group.id,
            service_ids=sample_service_ids,
        )

        assert response2["service_group_id"] == service_group.id
        assert response2["added_service_ids"] == sample_service_ids[mid:]
        assert set(response2["already_present_service_ids"]) == set(sample_service_ids_batch_1)
        assert response2["not_found_service_ids"] == []

        for service_id in sample_service_ids:
            assert ServiceGroupMember.objects.filter(
                group=service_group,
                service_id=service_id,
            ).exists()

        with pytest.raises(PermissionDenied):
            add_services_to_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                service_group_id=service_group.id,
                service_ids=[9999],
            )


@pytest.mark.django_db
class TestCreateRule:
    def test_create_rule(self, request_with_session, create_testing_tenant, db):
        filter_obj = create_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Filter",
            description="This is a test filter",
        )
        rule = create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            filter=filter_obj,
            enable=True,
            name="Test Rule",
            description="This is a test rule",
            rule_sequence=1,
            action="accept",
            log_type="log",
            hit_count=0,
        )
        assert rule is not None
        assert rule.name == "Test Rule"
        assert rule.description == "This is a test rule"
        assert rule.tenant_id == request_with_session.tenant_id
        assert rule.action == "accept"
        assert rule.log_type == "log"


@pytest.mark.django_db
class TestCreateFilter:
    def test_create_filter(self, request_with_session, create_testing_tenant):
        filter_obj = create_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Filter",
            description="This is a test filter",
        )
        assert filter_obj is not None
        assert filter_obj.name == "Test Filter"
        assert filter_obj.description == "This is a test filter"
        assert filter_obj.tenant_id == request_with_session.tenant_id
        assert filter_obj.enable is True


@pytest.mark.django_db
class TestMatchRuleToObjects:
    def test_add_objects_to_rule(
        self, sample_rules, sample_addresses, sample_services, request_with_session, create_testing_tenant
    ):
        rule_id = sample_rules[0].id

        add_objects_to_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=rule_id,
            match_type="source",
            objects=sample_addresses,
        )

        add_objects_to_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=rule_id,
            match_type="destination",
            objects=sample_services,
        )
        assert RuleMatch.objects.filter(rule_id=rule_id, match="source").count() == len(sample_addresses)
        assert RuleMatch.objects.filter(rule_id=rule_id, match="destination").count() == len(sample_services)