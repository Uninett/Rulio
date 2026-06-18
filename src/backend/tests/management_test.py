from backend.objects.management.device import Device
from backend.objects.management.device_group import DeviceGroup
from backend.objects.management.device_group_member import DeviceGroupMember
from backend.objects.management.interface import Interface
from backend.objects.management.tenant import Tenant
from backend.objects.management.filter_interface import FilterInterface


class TestManagement:
    def test_import_management(self):
        # Test that imports work and we can use the classes
        assert Device is not None
        assert DeviceGroup is not None
        assert DeviceGroupMember is not None
        assert Interface is not None
        assert Tenant is not None
        assert FilterInterface is not None
