from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.device_group_member import DeviceGroupMember
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.filter_interface import FilterInterface


class TestTenantObjectsImports:
    def test_import_management(self):
        # Test that imports work and we can use the classes
        assert Device is not None
        assert DeviceGroup is not None
        assert DeviceGroupMember is not None
        assert Interface is not None
        assert Tenant is not None
        assert FilterInterface is not None
