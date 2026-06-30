import datetime
import os

import pytest
from django.core.exceptions import PermissionDenied

from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.filters.rule_match import RuleMatch
from backend.services.attribute_objects.create_attribute_objects import create_address, create_service
from backend.services.attribute_objects.create_attribute_objects import create_address_group, create_service_group
from backend.services.create import create_policy_from_filter
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.membership import (
    add_addresses_to_group,
    add_services_to_group,
    add_objects_to_rule,
    add_rule_to_filter,
)
from backend.services.generate_config import generate_config
from backend.utils.logger import set_up_logger
from constants import TEST_LOGPATH

logger = set_up_logger(__name__)


@pytest.mark.django_db
class TestCreateAddress:
    def test_create_address(self, request_with_session, create_testing_tenant):

        address = create_address(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
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
        assert address.tenant_id == request_with_session.tenant_id
        assert address.get_address()[0][0].__str__() == "192.168.1.1/32"
        assert address.get_address()[1][0].__str__() == "2001:db8::1/128"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type == "standard"


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
        rule = create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Rule",
            description="This is a test rule",
            action="allow",
            log_type="log",
            hit_count=0,
        )
        assert rule is not None
        assert rule.name == "Test Rule"
        assert rule.description == "This is a test rule"
        assert rule.tenant_id == request_with_session.tenant_id
        assert rule.action == "allow"
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


@pytest.mark.django_db
class TestGenerateConfigFromFilterObject:
    def test_generate_config_from_simple_filter_object(
        self, sample_filters, sample_rules, request_with_session, create_testing_tenant, sample_addresses
    ):
        filter_id = sample_filters[0].id
        rule_id = sample_rules[0].id

        add_rule_to_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=rule_id,
            filter_id=filter_id,
            rule_sequence=10,
        )
        logger.info(
            f"Added rule {rule_id} to filter {filter_id} with rule_sequence 10, respone:\n{add_rule_to_filter.__name__}"
        )

        # Match the rule to the filter
        response = add_objects_to_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=rule_id,
            match_type="source",
            objects=[sample_addresses[0]],
        )

        assert response["error_count"] == 0
        assert response["added_count"] > 0
        logger.info(f"Matched rule {rule_id} to filter {filter_id}, response:\n{response}")
        vendor = "juniper"
        # Now generate the policy from the filter object
        policy = create_policy_from_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            filter_id=sample_filters[0].id,
            policy_sequence=10,
            vendor=vendor,
            policy_type="",
        )
        assert policy is not None

        config = generate_config(policy)

        filepath = TEST_LOGPATH / "from_filter" / f"{vendor.upper()}_simple_generated_config.yaml"
        os.makedirs(TEST_LOGPATH / "from_filter", exist_ok=True)

        for filename, content in config.items():
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

    def test_generate_config_from_complex_filter_object(
        self,
        sample_filters,
        sample_rules,
        request_with_session,
        realistic_acl_addresses,
        realistic_acl_services,
        realistic_acl_address_groups,
        realistic_acl_service_groups,
    ):
        filter_id = sample_filters[1].id
        rules = [
            sample_rules[0].id,
            sample_rules[1].id,
            sample_rules[2].id,
            sample_rules[3].id,
        ]

        for i, rule_id in enumerate(rules):
            add_rule_to_filter(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rule_id,
                filter_id=filter_id,
                rule_sequence=(i + 1) * 10,
            )
            logger.info(
                f"Added rule {rule_id} to filter {filter_id} with rule_sequence {(i + 1) * 10}, respone:\n{add_rule_to_filter.__name__}"
            )
        responses = [
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[0],
                match_type="source",
                objects=realistic_acl_addresses,
            ),
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[1],
                match_type="destination",
                objects=realistic_acl_services,
            ),
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[2],
                match_type="source",
                objects=realistic_acl_address_groups,
            ),
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[3],
                match_type="destination",
                objects=realistic_acl_service_groups,
            ),
        ]
        assert all(response["error_count"] == 0 for response in responses)

        vendor = "juniper"
        # Now generate the policy from the filter object
        policy = create_policy_from_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            filter_id=sample_filters[1].id,
            policy_sequence=10,
            vendor=vendor,
            policy_type="",
        )
        assert policy is not None

        filepath = TEST_LOGPATH / "from_filter" / f"{vendor.upper()}_complex_generated_config.yaml"
        os.makedirs(TEST_LOGPATH / "from_filter", exist_ok=True)

        config = generate_config(policy)
        for filename, content in config.items():
            logger.info(
                "\n=== Generated config: %s ===\n%s\n=== End config ===",
                filename,
                content,
            )
            with open(filepath, "w") as f:
                f.write(
                    f"# Generated on {datetime.datetime.now()}\n# Test for generating using complex filter objects\n\n"
                )
                f.write(content)
