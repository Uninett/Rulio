import datetime
import os

import pytest

from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.filters.filter import Filter
from backend.services.create import (
    add_addresses_to_group,
    add_rule_to_filter,
    create_address,
    create_address_group,
    create_config_from_filter,
    create_filter,
    create_rule,
    create_service,
    create_service_group,
    add_services_to_group,
    match_rule_to_objects,
)
from backend.tests.conftest import sample_filter
from backend.utils.logger import set_up_logger
from constants import TEST_LOGPATH

logger = set_up_logger(__name__)


@pytest.mark.django_db
class TestCreateAddress:
    def test_create_address(self, request_with_session, create_testing_tenant):

        request = request_with_session
        address = create_address(
            request=request,
            name="Test Address",
            description="This is a test address",
            addr_type="host",
            ipv4_type="standard",
            ipv6_type="standard",
            ipv4Network="192.168.1.1",
            ipv6Network="2001:db8::1",
        )
        assert address is not None
        assert address.name == "Test Address"
        assert address.description == "This is a test address"
        assert address.tenant_id == create_testing_tenant.id
        assert address.get_address()[0][0].__str__() == "192.168.1.1/32"
        assert address.get_address()[1][0].__str__() == "2001:db8::1/128"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type == "standard"


@pytest.mark.django_db
class TestCreateService:
    def test_create_service(self, request_with_session, create_testing_tenant):
        request = request_with_session
        service = create_service(
            request=request,
            name="Test Service",
            description="This is a test service",
            protocol="TCP",
            port_start=80,
            port_end=80,
        )
        assert service is not None
        assert service.name == "Test Service"
        assert service.description == "This is a test service"
        assert service.tenant_id == create_testing_tenant.id
        assert service.protocol == "TCP"
        assert service.port_start == 80
        assert service.port_end == 80


@pytest.mark.django_db
class TestCreateAddressGroup:
    def test_create_address_group(self, request_with_session, create_testing_tenant):
        request = request_with_session
        address_group = create_address_group(
            request=request,
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
        request = request_with_session
        service_group = create_service_group(
            request=request,
            name="Test Service Group",
            description="This is a test service group",
        )
        assert service_group is not None
        assert service_group.name == "Test Service Group"
        assert service_group.description == "This is a test service group"
        assert service_group.tenant_id == create_testing_tenant.id


@pytest.mark.django_db
class TestAddAddressToGroup:
    def test_add_address_to_group(self, sample_addresses, request_with_session):
        request = request_with_session
        sample_address_ids = [address.id for address in sample_addresses]
        address_group = create_address_group(
            request=request,
            name="Test Address Group",
            description="This is a test address group",
        )
        response = add_addresses_to_group(
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
class TestAddServicesToGroup:
    def test_add_services_to_group(self, sample_services, request_with_session):
        request = request_with_session
        service_group = create_service_group(
            request=request,
            name="Test Service Group",
            description="This is a test service group",
        )
        sample_service_ids = [service.id for service in sample_services]
        count_sample_services = len(sample_service_ids)
        mid = count_sample_services // 2
        sample_service_ids_batch_1 = sample_service_ids[:mid]

        response1 = add_services_to_group(service_group.id, sample_service_ids_batch_1)

        assert response1["service_group_id"] == service_group.id
        assert response1["added_service_ids"] == sample_service_ids_batch_1
        assert response1["not_found_service_ids"] == []
        assert response1["already_present_service_ids"] == []

        for service_id in sample_service_ids_batch_1:
            assert ServiceGroupMember.objects.filter(
                group_id=service_group.id,
                service_id=service_id,
            ).exists()

        response2 = add_services_to_group(service_group.id, sample_service_ids)

        assert response2["service_group_id"] == service_group.id
        assert response2["added_service_ids"] == sample_service_ids[mid:]
        assert set(response2["already_present_service_ids"]) == set(sample_service_ids_batch_1)
        assert response2["not_found_service_ids"] == []

        for service_id in sample_service_ids:
            assert ServiceGroupMember.objects.filter(
                group=service_group,
                service_id=service_id,
            ).exists()

        response3 = add_services_to_group(service_group.id, [9999])

        assert response3["service_group_id"] == service_group.id
        assert response3["added_service_ids"] == []
        assert response3["already_present_service_ids"] == []
        assert response3["not_found_service_ids"] == [9999]


@pytest.mark.django_db
class TestCreateRule:
    def test_create_rule(self, request_with_session, create_testing_tenant, db):
        request = request_with_session
        rule = create_rule(
            request=request,
            name="Test Rule",
            description="This is a test rule",
            action="allow",
            log_type="log",
            hit_count=0,
            direction="source",
        )
        assert rule is not None
        assert rule.name == "Test Rule"
        assert rule.description == "This is a test rule"
        assert rule.tenant == create_testing_tenant
        assert rule.action == "allow"
        assert rule.log_type == "log"
        assert rule.direction == "source"


@pytest.mark.django_db
class TestCreateFilter:
    def test_create_filter(self, request_with_session, create_testing_tenant):
        request = request_with_session
        filter_obj = create_filter(
            request=request,
            name="Test Filter",
            description="This is a test filter",
            enable=True,
        )
        assert filter_obj is not None
        assert filter_obj.name == "Test Filter"
        assert filter_obj.description == "This is a test filter"
        assert filter_obj.tenant_id == create_testing_tenant.id
        assert filter_obj.enable is True


@pytest.mark.django_db
class TestMatchRuleToObjects:
    def test_match_rule_to_objects(
        self, sample_rule, sample_addresses, sample_services, request_with_session, create_testing_tenant
    ):
        request = request_with_session
        rule_id = sample_rule.id
        match_type = "address"
        object_type = "address"

        match_rule_to_objects(
            request=request,
            rule_id=rule_id,
            match_type=match_type,
            object_type=object_type,
            object_ids=[address.id for address in sample_addresses],
        )


@pytest.mark.django_db
class GenerateConfigFromFilterObject:
    def test_generate_config_from_filter_object(
        self, sample_filter, sample_rule, request_with_session, create_testing_tenant
    ):
        request = request_with_session
        filter_id = sample_filter.id
        rule_id = sample_rule.id

        add_rule_to_filter(request=request, rule_id=rule_id, filter_id=filter_id, sequence=10)
        logger.info(
            f"Added rule {rule_id} to filter {filter_id} with sequence 10, respone:\n{add_rule_to_filter.__name__}"
        )

        # Match the rule to the filter
        match_rule_to_objects(
            request=request, rule_id=rule_id, match_type="filter", object_type=Filter, object_ids=[filter_id]
        )
        logger.info(f"Matched rule {rule_id} to filter {filter_id}, response:\n{match_rule_to_objects.__name__}")
        vendor = "JUNIPER"
        # Now generate the configuration from the filter object
        config = create_config_from_filter(request_with_session, sample_filter.id, vendor, policy_type="")
        print(config)
        filepath = TEST_LOGPATH / "from_filter" / f"{vendor.upper()}_generated_config.yaml"
        os.makedirs(TEST_LOGPATH / "from_filter", exist_ok=True)

        for filename, content in config.items():
            if vendor in self.log_for_vendors:
                logger.info(
                    "\n=== Generated config: %s ===\n%s\n=== End config ===",
                    filename,
                    content,
                )
            with open(filepath, "w") as f:
                f.write(
                    f"# Generated on {datetime.datetime.now()}\n# Test for generating using only Address objects\n\n"
                )
                f.write(content)
