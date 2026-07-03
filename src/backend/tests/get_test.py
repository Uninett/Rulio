import pytest

from django.core.exceptions import ObjectDoesNotExist
from backend.objects.attributes.address import Address
from backend.services.get import get_object_by_type_and_id, get_all_objects_with_certain_tag
from backend.services.membership import add_tag_to_object


@pytest.mark.django_db
class TestGetObjectByTypeAndId:
    def test_object_exists(self, sample_addresses):
        address = Address.objects.get(id=sample_addresses[0].id)
        assert address is not None
        assert isinstance(address, Address)

    def test_get_object_by_type_and_id_valid(self, sample_addresses, request_with_session):
        address = get_object_by_type_and_id(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            object_type="address",
            object_id=sample_addresses[0].id,
        )
        assert address is not None
        assert isinstance(address, Address)

    def test_get_object_by_type_and_id_invalid_type(self, request_with_session):
        with pytest.raises(ValueError) as excinfo:
            get_object_by_type_and_id(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                object_type="invalidType",
                object_id=1,
            )
        assert "Unsupported object type" in str(excinfo.value)

    def test_get_object_by_type_and_id_nonexistent_id(self, request_with_session):
        with pytest.raises(ObjectDoesNotExist, match="does not exist"):
            get_object_by_type_and_id(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                object_type="address",
                object_id=9999,
            )  # Assuming ID 9999 does not exist


@pytest.mark.django_db
class TestGetObjectsFromTags:
    def test_get_objects_from_certain_tag(
        self,
        sample_addresses,
        sample_interfaces,
        sample_tags,
        request_with_session,
    ):
        for address in sample_addresses:
            add_tag_to_object(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                tag=sample_tags[0],
                obj=address,
            )

        for interface in sample_interfaces:
            add_tag_to_object(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                tag=sample_tags[0],
                obj=interface,
            )

        _, tagged_objects = get_all_objects_with_certain_tag(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            tag_id=sample_tags[0].id,
        )

        for address in sample_addresses:
            assert address in tagged_objects["address"]

        for interface in sample_interfaces:
            assert interface in tagged_objects["interface"]
