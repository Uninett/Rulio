
import pytest

from backend.objects.management import (
            Device, DeviceGroup, DeviceGroupMember,
            Interface, Tenant, FilterInterface) 

class TestManagement:
    
    def test_import_management(self):
        # Test that imports work and we can use the classes
        assert Device is not None
        assert DeviceGroup is not None
        assert DeviceGroupMember is not None
        assert Interface is not None
        assert Tenant is not None
        assert FilterInterface is not None