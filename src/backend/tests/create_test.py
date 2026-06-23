import pytest

from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.services.create import (
    add_addresses_to_group,
    create_address,
    create_address_group,
    create_service,
    create_service_group,
    add_services_to_group,
)
from constants import TESTING_TENANT_ID


@pytest.mark.django_db
class TestCreateAddress:
    def test_create_address(self, request_with_session):

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
        assert address.tenant_id == TESTING_TENANT_ID
        assert address.get_address()[0][0].__str__() == "192.168.1.1/32"
        assert address.get_address()[1][0].__str__() == "2001:db8::1/128"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type == "standard"


@pytest.mark.django_db
class TestCreateService:
    def test_create_service(self, request_with_session):
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
        assert service.tenant_id == TESTING_TENANT_ID
        assert service.protocol == "TCP"
        assert service.port_start == 80
        assert service.port_end == 80


@pytest.mark.django_db
class TestCreateAddressGroup:
    def test_create_address_group(self, request_with_session):
        request = request_with_session
        address_group = create_address_group(
            request=request,
            name="Test Address Group",
            description="This is a test address group",
        )
        assert address_group is not None
        assert address_group.name == "Test Address Group"
        assert address_group.description == "This is a test address group"
        assert address_group.tenant_id == TESTING_TENANT_ID


@pytest.mark.django_db
class TestCreateServiceGroup:
    def test_create_service_group(self, request_with_session):
        request = request_with_session
        service_group = create_service_group(
            request=request,
            name="Test Service Group",
            description="This is a test service group",
        )
        assert service_group is not None
        assert service_group.name == "Test Service Group"
        assert service_group.description == "This is a test service group"
        assert service_group.tenant_id == TESTING_TENANT_ID


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
