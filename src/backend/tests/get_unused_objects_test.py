import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.get_unused_objects import (
    get_unused_address_objects,
    get_unused_filters,
    get_unused_service_objects,
    get_unused_tag_objects,
)
from backend.services.membership import (
    add_address_to_group,
    add_filter_to_interface,
    add_objects_to_rule,
    add_service_to_group,
    add_tag_to_object,
)
from backend.services.tenant_objects.create_tenant_objects import create_device, create_interface


@pytest.mark.django_db
class TestGetUnusedAddressObjects:
    def test_returns_unused_addresses_and_address_groups(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        unused_address = Address.objects.create(
            name="unused-address",
            description="unused",
            tenant_id=tenant_id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.10.10.0/24",
        )

        unused_group = AddressGroup.objects.create(
            tenant_id=tenant_id,
            name="unused-group",
            description="unused",
        )

        unused_addresses, unused_groups = get_unused_address_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert unused_address in unused_addresses
        assert unused_group in unused_groups

    def test_excludes_directly_used_address(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        filter_obj = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="address-filter-direct",
            description="filter for direct address usage",
        )
        rule = create_rule(
            actor=user,
            tenant_id=tenant_id,
            filter=filter_obj,
            name="address-rule-direct",
            description="rule using address directly",
            action="accept",
            enable=True,
            log_type="session_init",
            hit_count=0,
        )

        used_address = Address.objects.create(
            name="used-address-direct",
            description="used directly in rule",
            tenant_id=tenant_id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.20.20.0/24",
        )

        add_objects_to_rule(
            actor=user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="source",
            objects=[used_address],
        )

        unused_addresses, _ = get_unused_address_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert used_address not in unused_addresses

    def test_excludes_address_used_via_used_group(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        filter_obj = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="address-filter-group",
            description="filter for group address usage",
        )
        rule = create_rule(
            actor=user,
            tenant_id=tenant_id,
            filter=filter_obj,
            name="address-rule-group",
            description="rule using address group",
            action="accept",
            enable=True,
            log_type="session_init",
            hit_count=0,
        )

        grouped_address = Address.objects.create(
            name="grouped-address",
            description="used via group",
            tenant_id=tenant_id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.30.30.0/24",
        )

        used_group = AddressGroup.objects.create(
            tenant_id=tenant_id,
            name="used-address-group",
            description="group used by rule",
        )

        add_address_to_group(
            actor=user,
            tenant_id=tenant_id,
            address_group_id=used_group.id,
            address_id=grouped_address.id,
        )

        add_objects_to_rule(
            actor=user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="source",
            objects=[used_group],
        )

        unused_addresses, _ = get_unused_address_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert grouped_address not in unused_addresses

    def test_excludes_used_address_group(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        filter_obj = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="address-filter-used-group",
            description="filter for used address group",
        )
        rule = create_rule(
            actor=user,
            tenant_id=tenant_id,
            filter=filter_obj,
            name="address-rule-used-group",
            description="rule using address group directly",
            action="accept",
            enable=True,
            log_type="session_init",
            hit_count=0,
        )

        used_group = AddressGroup.objects.create(
            tenant_id=tenant_id,
            name="directly-used-group",
            description="used directly",
        )

        add_objects_to_rule(
            actor=user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="destination",
            objects=[used_group],
        )

        _, unused_groups = get_unused_address_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert used_group not in unused_groups


@pytest.mark.django_db
class TestGetUnusedServiceObjects:
    def test_returns_unused_services_and_service_groups(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        unused_service = Service.objects.create(
            tenant_id=tenant_id,
            name="unused-service",
            description="unused service",
            protocol="tcp",
            port_start=443,
            port_end=443,
        )

        unused_group = ServiceGroup.objects.create(
            tenant_id=tenant_id,
            name="unused-service-group",
            description="unused service group",
        )

        unused_services, unused_groups = get_unused_service_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert unused_service in unused_services
        assert unused_group in unused_groups

    def test_excludes_directly_used_service(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        filter_obj = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="service-filter-direct",
            description="filter for direct service usage",
        )
        rule = create_rule(
            actor=user,
            tenant_id=tenant_id,
            filter=filter_obj,
            name="service-rule-direct",
            description="rule using service directly",
            action="accept",
            enable=True,
            log_type="session_init",
            hit_count=0,
        )

        used_service = Service.objects.create(
            tenant_id=tenant_id,
            name="used-service-direct",
            description="used directly in rule",
            protocol="tcp",
            port_start=8443,
            port_end=8443,
        )

        add_objects_to_rule(
            actor=user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="destination",
            objects=[used_service],
        )

        unused_services, _ = get_unused_service_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert used_service not in unused_services

    def test_excludes_service_used_via_used_group(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        filter_obj = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="service-filter-group",
            description="filter for service group usage",
        )
        rule = create_rule(
            actor=user,
            tenant_id=tenant_id,
            filter=filter_obj,
            name="service-rule-group",
            description="rule using service group",
            action="accept",
            enable=True,
            log_type="session_init",
            hit_count=0,
        )

        grouped_service = Service.objects.create(
            tenant_id=tenant_id,
            name="grouped-service",
            description="used via group",
            protocol="udp",
            port_start=53,
            port_end=53,
        )

        used_group = ServiceGroup.objects.create(
            tenant_id=tenant_id,
            name="used-service-group",
            description="group used by rule",
        )

        add_service_to_group(
            actor=user,
            tenant_id=tenant_id,
            service_group_id=used_group.id,
            service_id=grouped_service.id,
        )

        add_objects_to_rule(
            actor=user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="destination",
            objects=[used_group],
        )

        unused_services, _ = get_unused_service_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert grouped_service not in unused_services

    def test_excludes_used_service_group(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        filter_obj = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="service-filter-used-group",
            description="filter for directly used service group",
        )
        rule = create_rule(
            actor=user,
            tenant_id=tenant_id,
            filter=filter_obj,
            name="service-rule-used-group",
            description="rule using service group directly",
            action="accept",
            enable=True,
            log_type="session_init",
            hit_count=0,
        )

        used_group = ServiceGroup.objects.create(
            tenant_id=tenant_id,
            name="directly-used-service-group",
            description="used directly",
        )

        add_objects_to_rule(
            actor=user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="destination",
            objects=[used_group],
        )

        _, unused_groups = get_unused_service_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert used_group not in unused_groups


@pytest.mark.django_db
class TestGetUnusedTagObjects:
    def test_returns_only_unused_tags(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        unused_tag = Tag.objects.create(
            tenant_id=tenant_id,
            name="unused-tag",
            description="not connected to anything",
        )

        used_tag = Tag.objects.create(
            tenant_id=tenant_id,
            name="used-tag",
            description="connected to an object",
        )

        address = Address.objects.create(
            name="tag-target-address",
            description="address tagged by used-tag",
            tenant_id=tenant_id,
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.40.40.0/24",
        )

        add_tag_to_object(
            actor=user,
            tenant_id=tenant_id,
            tag=used_tag,
            obj=address,
        )

        unused_tags = get_unused_tag_objects(
            actor=user,
            tenant_id=tenant_id,
        )

        assert unused_tag in unused_tags
        assert used_tag not in unused_tags


@pytest.mark.django_db
class TestGetUnusedFilters:
    def test_returns_only_filters_not_applied_to_interfaces(self, authenticated_user_and_tenant_id):
        user, tenant_id = authenticated_user_and_tenant_id

        unused_filter = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="unused-filter",
            description="not attached to any interface",
        )

        used_filter = create_filter(
            actor=user,
            tenant_id=tenant_id,
            name="used-filter",
            description="attached to interface",
        )

        device = create_device(
            actor=user,
            tenant_id=tenant_id,
            name="unused-filter-device",
            description="device for filter-interface test",
            platform="juniper",
            type="firewall",
        )

        interface = create_interface(
            actor=user,
            tenant_id=tenant_id,
            device_id=device.id,
            name="eth0",
            description="test interface",
            type="physical",
        )

        add_filter_to_interface(
            actor=user,
            tenant_id=tenant_id,
            interface_id=interface.id,
            filter_id=used_filter.id,
            direction="in",
            enable=True,
            policy_sequence=1,
        )

        unused_filters = get_unused_filters(
            actor=user,
            tenant_id=tenant_id,
        )

        assert unused_filter in unused_filters
        assert used_filter not in unused_filters
