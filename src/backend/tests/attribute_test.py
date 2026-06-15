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

    def test_ipv4_address(self):
        address = Address(
            name="Test Address",
            description="This is a test address",
            tenant_id=42,
            type="ipv4",
            ipv4_value="127.0.0.1",
            ipv6_value=None,
        )
        assert (
            str(address)
            == "Address(id=1, name='Test Address', description='This is a test address', tenant_id=42, type='ipv4', ipv4_value='127.0.0.1', ipv6_value='None')"
        )

    def test_ipv6_address(self):
        address = Address(
            name="Test Address",
            description="This is a test address",
            tenant_id=42,
            type="ipv6",
            ipv4_value=None,
            ipv6_value="2001:db8::1",
        )
        assert (
            str(address)
            == "Address(id=1, name='Test Address', description='This is a test address', tenant_id=42, type='ipv6', ipv4_value='None', ipv6_value='2001:db8::1')"
        )

    def test_get_address(self):
        address = Address(
            name="Test Address",
            description="This is a test address",
            tenant_id=42,
            type="ipv4",
            ipv4_value="127.2.4.2/31",
            ipv6_value=None,
        )
        assert address.get_address() == "127.2.4.2/31"


    def test_service(self):
        service = Service(
            name="Test Service",
            description="This is a test service",
            tenant_id=42,
            protocol="tcp",
            port_start=80,
            port_end=80,
        )
        assert service.get_ports() == "80"
        assert service.get_protocol() == "tcp"

            
