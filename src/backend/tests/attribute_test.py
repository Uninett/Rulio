


from backend.objects.attributes import (
            Address, AddressGroup, AddressGroupMember,
            Service, ServiceGroup, ServiceGroupMember,
            Tag, TagObject
        )

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
