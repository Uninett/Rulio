


from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_object import TagObject
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember


class TestAttributes:
    
    def test_import_attributes(self):
        # Test that imports work and we can use the classes
        assert Address is not None
        assert AddressGroup is not None
        assert AddressGroupMember is not None
        assert Service is not None
        assert ServiceGroup is not None
        assert ServiceGroupMember is not None
        assert Tag is not None
        assert TagObject is not None
