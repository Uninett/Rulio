import ipaddress

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
            ipv4_type="standard",
            ipv4Network="127.0.0.1",
        )
        assert str(address.get_address()[0][0]) == "127.0.0.1/32"

    def test_ipv6_address(self):
        address = Address(
            name="Test Address",
            description="This is a test address",
            tenant_id=42,
            ipv6_type="standard",
            ipv6Network="2001:db8::/64",
        )
        assert str(address.get_address()[1][0]) == "2001:db8::/64"

    def test_get_address(self):
        address = Address(
            name="Test Address",
            description="This is a test address",
            tenant_id=42,
            ipv4_type="standard",
            ipv4Network="127.2.4.2/31",
        )
        assert str(address.get_address()[0][0]) == "127.2.4.2/31"

    def test_custom_range(self):
        address = Address(
            name="Test Address",
            description="This is a test address",
            tenant_id=42,
            ipv4_type="custom_range",
            ipv4Address_start="127.2.4.2",
            ipv4Address_end="127.2.4.17",
        )
        assert address.get_address()[0] == list(
            ipaddress.summarize_address_range(ipaddress.IPv4Address("127.2.4.2"), ipaddress.IPv4Address("127.2.4.17"))
        )

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
