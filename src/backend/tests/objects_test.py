from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_filter import RuleFilter
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.filters.versionControl import VersionControl
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.device_group_member import DeviceGroupMember
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.filter_interface import FilterInterface


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
        assert TagConnection is not None
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
