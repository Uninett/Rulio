import pytest

from backend.services.create import create_address


class TestCreate:
    @pytest.mark.django_db
    def test_create_address(self):
        class MockRequest:
            session = {"current_tenant_id": 42}

        request = MockRequest()
        address = create_address(
            request=request,
            name="Test Address",
            description="This is a test address",
            ipv4_type="standard",
            ipv6_type="standard",
            ipv4Network="192.168.1.1",
            ipv6Network="2001:db8::1",
        )
        assert address is not None
        assert address.name == "Test Address"
        assert address.description == "This is a test address"
        assert address.tenant_id == 42
        assert address.get_address()[0][0].__str__() == "192.168.1.1/32"
        assert address.get_address()[1][0].__str__() == "2001:db8::1/128"
        assert address.ipv4_type == "standard"
        assert address.ipv6_type == "standard"
