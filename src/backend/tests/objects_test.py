import pytest

from backend.objects import Address, AddressGroup, AddressGroupMember, Service, ServiceGroup, ServiceGroupMember, Tag, TagObject, Device, DeviceGroup, DeviceGroupMember, Interface, Tenant, FilterInterface, Filter, Rule, RuleFilter, RuleMatch, VersionControl

class TestObjects: 
    
    def test_import_objects(self):
        # Test that importing all objects works
        assert Address is not None
        assert AddressGroup is not None
        assert AddressGroupMember is not None
        assert Service is not None
        assert ServiceGroup is not None
        assert ServiceGroupMember is not None
        assert Tag is not None
        assert TagObject is not None
        assert Filter is not None
        assert Rule is not None
        assert RuleFilter is not None
        assert RuleMatch is not None
        assert VersionControl is not None
        assert Device is not None
        assert DeviceGroup is not None
        assert DeviceGroupMember is not None
        assert Interface is not None
        assert Tenant is not None
        assert FilterInterface is not None