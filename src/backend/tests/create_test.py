import pytest

from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.services.create import (
    create_address,
    create_service,
    create_service_group,
    add_services_to_group,
)


class MockRequest:
    session = {"current_tenant_id": 42}


@pytest.mark.django_db
class TestCreateAddress:
    def test_create_address(self):

        request = MockRequest()
        address = create_address(
            request=request,
            name="Test Address",
            description="This is a test address",
            ipv4_type="standard",
            ipv6_type="standard",
            ipv4Network="192.168.1.1",
            ipv6Network="2001:db8::1",
        )
        assert address is not None
        assert address.name == "Test Address"
        assert address.description == "This is a test address"
        assert address.tenant_id == 42
        assert address.get_address()[0][0].__str__() == "192.168.1.1/32"
        assert address.get_address()[1][0].__str__() == "2001:db8::1/128"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type == "standard"


@pytest.mark.django_db
class TestCreateService:
    def test_create_service(self):
        request = MockRequest()
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
        assert service.tenant_id == 42
        assert service.protocol == "TCP"
        assert service.port_start == 80
        assert service.port_end == 80


@pytest.mark.django_db
class TestCreateServiceGroup:
    def test_create_service_group(self):
        request = MockRequest()
        service_group = create_service_group(
            request=request,
            name="Test Service Group",
            description="This is a test service group",
        )
        assert service_group is not None
        assert service_group.name == "Test Service Group"
        assert service_group.description == "This is a test service group"


@pytest.mark.django_db
class TestAddServicesGroup:
    def test_add_services_group(self):
        request = MockRequest
        service_group = create_service_group(
            request=request,
            name="Test Service Group",
            description="This is a test service group",
        )
        service = create_service(
            request=request,
            name="Test Service",
            description="This is a test service",
            protocol="TCP",
            port_start=80,
            port_end=80,
        )

        response = add_services_to_group(service_group.id, [service.id, 999])

        assert response["service_group_id"] == service_group.id
        assert response["added_service_ids"] == [service.id]
        assert response["not_found_service_ids"] == [999]
        assert response["already_present_service_ids"] == []

        assert ServiceGroupMember.objects.filter(
            group=service_group,
            service=service,
        ).exists()
