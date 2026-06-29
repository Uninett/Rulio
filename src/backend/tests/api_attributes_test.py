import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
import json

from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup


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


@pytest.mark.django_db
def test_api_add_addresses_to_group_invalid_group(authenticated_client_with_tenant):
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

    invalid_group_id = 9999

    response = client.post(
        f"/api/add_addresses_to_group?group_id={invalid_group_id}",
        data=json.dumps(addresses),
        content_type="application/json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_api_create_and_add_address_to_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    client.post(
        "/api/create_address_group",
        {"name": "test_group", "description": ""},
        content_type="application/json",
    )
    group_id = AddressGroup.objects.get(name="test_group").id
    address_payload = {
        "payload": {
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
        },
        "group_ids": [group_id],
    }
    response = client.post(
        "/api/create_and_add_address_to_groups", data=json.dumps(address_payload), content_type="application/json"
    )
    assert response.status_code == 200

    address_id = Address.objects.get(name="test_address").id

    data = client.get("/api/get_address_group_and_addresses").json()

    found = any(
        group["address_group_id"] == group_id
        and any(address["address_id"] == address_id for address in group["addresses"])
        for group in data
    )

    assert found


@pytest.mark.django_db
def test_api_create_address_group_and_add_addresses(authenticated_client_with_tenant):
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

    group_payload = {
        "payload": {
            "name": "test_group",
            "description": "",
        },
        "address_ids": addresses,
    }

    response = client.post(
        "/api/create_address_group_and_add_addresses", data=json.dumps(group_payload), content_type="application/json"
    )
    assert response.status_code == 200

    group_id = AddressGroup.objects.get(name="test_group").id

    data = client.get("/api/get_address_group_and_addresses").json()

    group = next((g for g in data if g["address_group_id"] == group_id), None)

    assert group is not None

    returned_address_ids = [address["address_id"] for address in group["addresses"]]

    assert all(address_id in returned_address_ids for address_id in addresses)


@pytest.mark.django_db
def test_api_delete_address(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "test_address_to_delete",
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
    response = client.post("/api/create_address", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

    address_id = Address.objects.get(name="test_address_to_delete").id

    response = client.delete(f"/api/delete_address?address_id={address_id}", content_type="application/json")
    assert response.status_code == 200

    with pytest.raises(Address.DoesNotExist):
        Address.objects.get(id=address_id)


@pytest.mark.django_db
def test_api_delete_address_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "test_group_to_delete",
        "description": "",
    }
    response = client.post("/api/create_address_group", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

    group_id = AddressGroup.objects.get(name="test_group_to_delete").id

    response = client.delete(f"/api/delete_address_group?group_id={group_id}", content_type="application/json")
    assert response.status_code == 200

    with pytest.raises(AddressGroup.DoesNotExist):
        AddressGroup.objects.get(id=group_id)


@pytest.mark.django_db
def test_api_create_service(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "test_service",
        "description": "",
        "protocol": "tcp",
        "port_start": 80,
        "port_end": 80,
    }

    response = client.post("/api/create_service", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

    service_id = Service.objects.filter(name="test_service").first().id
    assert service_id is not None

    service = Service.objects.get(id=service_id)
    assert service.name == "test_service"
    assert service.protocol == "TCP"
    assert service.port_start == 80
    assert service.port_end == 80


@pytest.mark.django_db
def test_api_create_service_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "test_service_group",
        "description": "",
    }

    response = client.post("/api/create_service_group", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

    group_id = ServiceGroup.objects.filter(name="test_service_group").first().id
    assert group_id is not None

    group = ServiceGroup.objects.get(id=group_id)
    assert group.name == "test_service_group"


@pytest.mark.django_db
def test_api_add_service_to_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    service_payload = {
        "name": "test_service",
        "description": "",
        "protocol": "tcp",
        "port_start": 80,
        "port_end": 80,
    }

    service_response = client.post(
        "/api/create_service", data=json.dumps(service_payload), content_type="application/json"
    )
    assert service_response.status_code == 200
    service_id = Service.objects.filter(name="test_service").first().id
    assert service_id is not None

    group_payload = {
        "name": "test_service_group",
        "description": "",
    }

    group_response = client.post(
        "/api/create_service_group", data=json.dumps(group_payload), content_type="application/json"
    )
    assert group_response.status_code == 200
    group_id = ServiceGroup.objects.filter(name="test_service_group").first().id
    assert group_id is not None

    add_response = client.post(f"/api/add_service_to_group?service_id={service_id}&group_id={group_id}")
    assert add_response.status_code == 200

    data = client.get("/api/get_service_group_and_services").json()

    found = any(
        group["service_group_id"] == group_id
        and any(service["service_id"] == service_id for service in group["services"])
        for group in data
    )

    assert found


@pytest.mark.django_db
def test_api_add_services_to_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    services = []

    for i in range(1, 4):
        payload = {
            "name": f"test_service_{i}",
            "description": "",
            "protocol": "tcp",
            "port_start": 80 + i,
            "port_end": 80 + i,
        }
        response = client.post("/api/create_service", data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 200

        service_id = Service.objects.get(name=f"test_service_{i}").id
        services.append(service_id)

    group_payload = {
        "name": "test_service_group",
        "description": "",
    }
    response = client.post("/api/create_service_group", data=json.dumps(group_payload), content_type="application/json")
    assert response.status_code == 200

    group_id = ServiceGroup.objects.get(name="test_service_group").id
    assert group_id is not None

    response = client.post(
        f"/api/add_services_to_group?group_id={group_id}",
        data=json.dumps(services),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = client.get("/api/get_service_group_and_services").json()

    group = next((g for g in data if g["service_group_id"] == group_id), None)

    assert group is not None

    returned_service_ids = [service["service_id"] for service in group["services"]]

    assert all(service_id in returned_service_ids for service_id in services)


@pytest.mark.django_db
def test_api_create_and_add_service_to_groups(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    client.post(
        "/api/create_service_group",
        {"name": "test_service_group", "description": ""},
        content_type="application/json",
    )
    group_id = ServiceGroup.objects.get(name="test_service_group").id
    service_payload = {
        "payload": {
            "name": "test_service",
            "description": "",
            "protocol": "tcp",
            "port_start": 80,
            "port_end": 80,
        },
        "group_ids": [group_id],
    }
    response = client.post(
        "/api/create_and_add_service_to_groups", data=json.dumps(service_payload), content_type="application/json"
    )
    assert response.status_code == 200

    service_id = Service.objects.get(name="test_service").id

    data = client.get("/api/get_service_group_and_services").json()

    found = any(
        group["service_group_id"] == group_id
        and any(service["service_id"] == service_id for service in group["services"])
        for group in data
    )

    assert found


@pytest.mark.django_db
def test_api_create_service_group_and_add_services(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    services = []

    for i in range(1, 4):
        payload = {
            "name": f"test_service_{i}",
            "description": "",
            "protocol": "tcp",
            "port_start": 80 + i,
            "port_end": 80 + i,
        }
        response = client.post("/api/create_service", data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 200

        service_id = Service.objects.get(name=f"test_service_{i}").id
        services.append(service_id)

    group_payload = {
        "payload": {
            "name": "test_service_group",
            "description": "",
        },
        "service_ids": services,
    }

    response = client.post(
        "/api/create_service_group_and_add_services", data=json.dumps(group_payload), content_type="application/json"
    )
    assert response.status_code == 200

    group_id = ServiceGroup.objects.get(name="test_service_group").id

    data = client.get("/api/get_service_group_and_services").json()

    group = next((g for g in data if g["service_group_id"] == group_id), None)

    assert group is not None

    returned_service_ids = [service["service_id"] for service in group["services"]]

    assert all(service_id in returned_service_ids for service_id in services)


@pytest.mark.django_db
def test_api_delete_service(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "test_service_to_delete",
        "description": "",
        "protocol": "tcp",
        "port_start": 80,
        "port_end": 80,
    }
    response = client.post("/api/create_service", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

    service_id = Service.objects.get(name="test_service_to_delete").id

    response = client.delete(f"/api/delete_service?service_id={service_id}", content_type="application/json")
    assert response.status_code == 200

    with pytest.raises(Service.DoesNotExist):
        Service.objects.get(id=service_id)


@pytest.mark.django_db
def test_api_delete_service_group(authenticated_client_with_tenant):
    client = authenticated_client_with_tenant

    payload = {
        "name": "test_service_group_to_delete",
        "description": "",
    }
    response = client.post("/api/create_service_group", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

    group_id = ServiceGroup.objects.get(name="test_service_group_to_delete").id

    response = client.delete(f"/api/delete_service_group?group_id={group_id}", content_type="application/json")
    assert response.status_code == 200

    with pytest.raises(ServiceGroup.DoesNotExist):
        ServiceGroup.objects.get(id=group_id)
