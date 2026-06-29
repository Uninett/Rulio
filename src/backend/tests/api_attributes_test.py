import pytest

from constants import GLOBAL_TENANT_ID


@pytest.mark.django_db
def test_api_create_address(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "string",
        "description": "",
        "ipv4Network": "192.168.0.0/24",
        "ipv4Address_start": None,
        "ipv4Address_end": None,
        "ipv6Network": "2001:db8::/32",
        "ipv6Address_start": None,
        "ipv6Address_end": None,
        "addr_type": "network",
        "ipv4_type": "standard",
        "ipv6_type": "standard",
    }

    response = client.post("/api/create_address", data=payload, content_type="application/json")
    print(response.json())

    assert response.status_code == 200
