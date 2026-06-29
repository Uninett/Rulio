import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
import json


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


@pytest.mark.django_db
def test_api_create_address_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "string",
        "description": "",
    }

    response = client.post("/api/create_address_group", data=payload, content_type="application/json")
    print(response.json())

    assert response.status_code == 200


@pytest.mark.django_db
def test_api_add_address_to_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    address_payload = {
        "name": "test_address",
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

    address_response = client.post("/api/create_address", data=address_payload, content_type="application/json")
    assert address_response.status_code == 200
    address_id = Address.objects.filter(name="test_address").first().id
    assert address_id is not None

    group_payload = {
        "name": "test_group",
        "description": "",
    }

    group_response = client.post("/api/create_address_group", data=group_payload, content_type="application/json")
    assert group_response.status_code == 200
    group_id = AddressGroup.objects.filter(name="test_group").first().id
    assert group_id is not None

    add_response = client.post(f"/api/add_address_to_group?address_id={address_id}&group_id={group_id}")
    assert add_response.status_code == 200

    data = client.get("/api/get_address_group_and_addresses").json()

    found = any(
        group["address_group_id"] == group_id
        and any(address["address_id"] == address_id for address in group["addresses"])
        for group in data
    )

    assert found


@pytest.mark.django_db
def test_api_add_addresses_to_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    addresses = []

    for i in range(1, 4):
        payload = {
            "name": f"test_address_{i}",
            "description": "",
            "ipv4Network": f"192.168.{i}.0/24",
            "ipv4Address_start": None,
            "ipv4Address_end": None,
            "ipv6Network": f"2001:db8:{i}::/48",
            "ipv6Address_start": None,
            "ipv6Address_end": None,
            "addr_type": "network",
            "ipv4_type": "standard",
            "ipv6_type": "standard",
        }
        response = client.post("/api/create_address", data=payload, content_type="application/json")
        assert response.status_code == 200

        address_id = Address.objects.get(name=f"test_address_{i}").id
        addresses.append(address_id)

    payload = {
        "name": "test_group",
        "description": "",
    }
    response = client.post("/api/create_address_group", data=payload, content_type="application/json")
    assert response.status_code == 200

    group_id = AddressGroup.objects.get(name="test_group").id
    assert group_id is not None

    response = client.post(
        f"/api/add_addresses_to_group?group_id={group_id}",
        data=json.dumps(addresses),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = client.get("/api/get_address_group_and_addresses").json()

    group = next((g for g in data if g["address_group_id"] == group_id), None)

    assert group is not None

    returned_address_ids = [address["address_id"] for address in group["addresses"]]

    assert all(address_id in returned_address_ids for address_id in addresses)
