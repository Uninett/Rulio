import pytest

from django.core.exceptions import ObjectDoesNotExist
from backend.objects.attributes.address import Address
from backend.services.get import get_object_by_type_and_id


@pytest.mark.django_db
class TestGetObjectByTypeAndId:
    def test_object_exists(self, sample_addresses):
        address = Address.objects.get(id=sample_addresses[0].id)
        assert address is not None
        assert isinstance(address, Address)

    def test_get_object_by_type_and_id_valid(self, sample_addresses):
        address = get_object_by_type_and_id("address", sample_addresses[0].id)
        assert address is not None
        assert isinstance(address, Address)

    def test_get_object_by_type_and_id_invalid_type(self):
        with pytest.raises(ValueError) as excinfo:
            get_object_by_type_and_id("invalidType", 1)
        assert "Unsupported object type" in str(excinfo.value)

    def test_get_object_by_type_and_id_nonexistent_id(self):
        with pytest.raises(ObjectDoesNotExist, match="does not exist"):
            get_object_by_type_and_id("address", 9999)  # Assuming ID 9999 does not exist
