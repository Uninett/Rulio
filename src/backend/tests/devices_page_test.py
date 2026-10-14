import json

import pytest
from django.urls import reverse

from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.interface import Interface
from backend.services.attribute_objects.create_attribute_objects import create_tag
from backend.services.tenant_objects.create_tenant_objects import create_device, create_interface
from backend.views.devices_page import InterfaceFields, parse_interface_fields, sync_device_interfaces


@pytest.fixture
def device_with_interfaces(authenticated_user_and_tenant_id):
    user, tenant_id = authenticated_user_and_tenant_id
    device = create_device(
        actor=user,
        tenant_id=tenant_id,
        name="Test_Device_Interfaces",
        platform="test-platform",
        description="Device used to test interface syncing",
        type="test-type",
    )
    for name in ("eth0", "eth1"):
        create_interface(
            actor=user,
            tenant_id=tenant_id,
            name=name,
            description="",
            device_id=device.id,
            type="",
        )
    return device


def interface_ids(device):
    return sorted(Interface.objects.filter(device=device).values_list("id", flat=True))


def post_device_update(client, device, **extra_fields):
    return client.post(
        f"/devices/{device.id}/update/",
        {
            "name": device.name,
            "description": "Updated description",
            "platform": device.platform,
            "type": device.type,
            **extra_fields,
        },
    )


# The device form sends an empty interface_fields value when the interface modal was never applied.
@pytest.mark.django_db
@pytest.mark.parametrize("extra_fields", [{}, {"interface_fields": ""}], ids=["missing", "empty"])
def test_update_device_without_interface_changes_keeps_interfaces(
    authenticated_client, device_with_interfaces, extra_fields
):
    before = interface_ids(device_with_interfaces)

    response = post_device_update(authenticated_client, device_with_interfaces, **extra_fields)

    assert response.status_code == 204
    assert interface_ids(device_with_interfaces) == before


@pytest.mark.django_db
def test_update_device_with_unchanged_interface_draft_keeps_interfaces(authenticated_client, device_with_interfaces):
    before = interface_ids(device_with_interfaces)
    draft = [
        {"id": interface.id, "name": interface.name, "description": "", "type": "", "vrf": ""}
        for interface in Interface.objects.filter(device=device_with_interfaces)
    ]

    response = post_device_update(authenticated_client, device_with_interfaces, interface_fields=json.dumps(draft))

    assert response.status_code == 204
    assert interface_ids(device_with_interfaces) == before


@pytest.mark.django_db
def test_update_device_with_emptied_interface_draft_deletes_interfaces(authenticated_client, device_with_interfaces):
    response = post_device_update(authenticated_client, device_with_interfaces, interface_fields="[]")

    assert response.status_code == 204
    assert interface_ids(device_with_interfaces) == []


# parse_interface_fields


@pytest.mark.parametrize("raw_value", [None, "", "not json", '"a string"', "42"])
def test_parse_interface_fields_returns_empty_list_for_missing_or_invalid_input(raw_value):
    assert parse_interface_fields(raw_value) == []


def test_parse_interface_fields_wraps_single_object_in_list():
    assert parse_interface_fields('{"name": "eth0"}') == [InterfaceFields(name="eth0")]


def test_parse_interface_fields_skips_entries_without_name():
    raw_value = json.dumps([{"name": "  "}, {"description": "no name"}, "not an object", {"name": " eth0 "}])

    assert parse_interface_fields(raw_value) == [InterfaceFields(name="eth0")]


@pytest.mark.parametrize(("raw_id", "expected_id"), [(5, 5), ("5", 5), ("abc", None), ("", None), (None, None)])
def test_parse_interface_fields_converts_id_to_int_where_possible(raw_id, expected_id):
    [interface_field] = parse_interface_fields(json.dumps([{"name": "eth0", "id": raw_id}]))

    assert interface_field.id == expected_id


def test_parse_interface_fields_reads_all_fields_and_uppercase_vrf_key():
    raw_value = json.dumps([{"name": "eth0", "description": "Uplink", "type": "physical", "VRF": "mgmt"}])

    assert parse_interface_fields(raw_value) == [
        InterfaceFields(name="eth0", description="Uplink", type="physical", vrf="mgmt")
    ]


# sync_device_interfaces


@pytest.mark.django_db
def test_sync_device_interfaces_renames_interface_matched_by_id(
    authenticated_user_and_tenant_id, device_with_interfaces
):
    user, tenant_id = authenticated_user_and_tenant_id
    eth0 = Interface.objects.get(device=device_with_interfaces, name="eth0")
    eth1 = Interface.objects.get(device=device_with_interfaces, name="eth1")

    sync_device_interfaces(
        actor=user,
        tenant_id=tenant_id,
        device=device_with_interfaces,
        interface_fields=[InterfaceFields(name="uplink", id=eth0.id), InterfaceFields(name="eth1", id=eth1.id)],
    )

    eth0.refresh_from_db()
    assert eth0.name == "uplink"
    assert interface_ids(device_with_interfaces) == sorted([eth0.id, eth1.id])


@pytest.mark.django_db
def test_sync_device_interfaces_matches_by_name_when_id_is_missing(
    authenticated_user_and_tenant_id, device_with_interfaces
):
    user, tenant_id = authenticated_user_and_tenant_id
    before = interface_ids(device_with_interfaces)

    sync_device_interfaces(
        actor=user,
        tenant_id=tenant_id,
        device=device_with_interfaces,
        interface_fields=[InterfaceFields(name="eth0", description="Re-added"), InterfaceFields(name="eth1")],
    )

    assert interface_ids(device_with_interfaces) == before
    assert Interface.objects.get(device=device_with_interfaces, name="eth0").description == "Re-added"


@pytest.mark.django_db
def test_sync_device_interfaces_creates_new_and_deletes_unlisted_interfaces(
    authenticated_user_and_tenant_id, device_with_interfaces
):
    user, tenant_id = authenticated_user_and_tenant_id
    eth0 = Interface.objects.get(device=device_with_interfaces, name="eth0")

    sync_device_interfaces(
        actor=user,
        tenant_id=tenant_id,
        device=device_with_interfaces,
        interface_fields=[InterfaceFields(name="eth0", id=eth0.id), InterfaceFields(name="eth2", vrf="mgmt")],
    )

    interfaces = {interface.name: interface for interface in Interface.objects.filter(device=device_with_interfaces)}
    assert set(interfaces) == {"eth0", "eth2"}
    assert interfaces["eth0"].id == eth0.id
    assert interfaces["eth2"].VRF == "mgmt"


# Interface modal


@pytest.mark.django_db
def test_device_interfaces_modal_loads_saved_interfaces(authenticated_client, device_with_interfaces):
    response = authenticated_client.get(reverse("device-interfaces-modal", args=[device_with_interfaces.id]))

    assert response.status_code == 200
    assert response.context["device_id"] == device_with_interfaces.id
    assert sorted(interface["name"] for interface in response.context["interfaces"]) == ["eth0", "eth1"]
    assert all(interface["id"] is not None for interface in response.context["interfaces"])


@pytest.mark.django_db
def test_device_interfaces_modal_shows_draft_instead_of_saved_interfaces(authenticated_client, device_with_interfaces):
    draft = json.dumps([{"id": None, "name": "draft-only"}])

    response = authenticated_client.get(
        reverse("device-interfaces-modal", args=[device_with_interfaces.id]), {"interface_fields": draft}
    )

    assert response.status_code == 200
    assert [interface["name"] for interface in response.context["interfaces"]] == ["draft-only"]


# An emptied draft must not fall back to the saved interfaces, or deleted rows would reappear in the modal.
@pytest.mark.django_db
def test_device_interfaces_modal_keeps_emptied_draft_empty(authenticated_client, device_with_interfaces):
    response = authenticated_client.get(
        reverse("device-interfaces-modal", args=[device_with_interfaces.id]), {"interface_fields": "[]"}
    )

    assert response.status_code == 200
    assert response.context["interfaces"] == []


@pytest.mark.django_db
def test_device_interfaces_modal_returns_404_for_missing_device(authenticated_client_with_tenant):
    response = authenticated_client_with_tenant.get(reverse("device-interfaces-modal", args=[999999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_new_device_interfaces_modal_starts_empty(authenticated_client_with_tenant):
    response = authenticated_client_with_tenant.get(reverse("new-device-interfaces-modal"))

    assert response.status_code == 200
    assert response.context["interfaces"] == []
    assert response.context["device_id"] is None


@pytest.mark.django_db
def test_new_device_interfaces_modal_shows_draft(authenticated_client_with_tenant):
    response = authenticated_client_with_tenant.get(
        reverse("new-device-interfaces-modal"), {"interface_fields": json.dumps([{"name": "eth0"}])}
    )

    assert response.status_code == 200
    assert [interface["name"] for interface in response.context["interfaces"]] == ["eth0"]


# Create and delete


@pytest.mark.django_db
def test_create_device_with_interfaces(authenticated_client_with_tenant, create_testing_tenant):
    response = authenticated_client_with_tenant.post(
        reverse("post-device-view"),
        {
            "name": "Test_New_Device",
            "description": "Created from the device form",
            "platform": "test-platform",
            "type": "test-type",
            "interface_fields": json.dumps([{"id": None, "name": "eth0"}, {"id": None, "name": "eth1", "vrf": "mgmt"}]),
        },
    )

    assert response.status_code == 200
    device = Device.objects.get(name="Test_New_Device", tenant_id=create_testing_tenant.id)
    interfaces = {interface.name: interface for interface in Interface.objects.filter(device=device)}
    assert set(interfaces) == {"eth0", "eth1"}
    assert interfaces["eth1"].VRF == "mgmt"


@pytest.mark.django_db
def test_create_device_with_missing_required_fields_returns_error(authenticated_client_with_tenant):
    device_count = Device.objects.count()

    response = authenticated_client_with_tenant.post(reverse("post-device-view"), {"name": ""})

    assert response.status_code == 400
    assert b"Could not create device" in response.content
    assert Device.objects.count() == device_count


@pytest.mark.django_db
def test_delete_device_removes_device_and_interfaces(authenticated_client, device_with_interfaces):
    device_id = device_with_interfaces.id

    response = authenticated_client.post(reverse("delete-device-view", args=[device_id]))

    assert response.status_code == 204
    assert not Device.objects.filter(id=device_id).exists()
    assert not Interface.objects.filter(device_id=device_id).exists()


@pytest.mark.django_db
def test_delete_missing_device_returns_error(authenticated_client_with_tenant):
    response = authenticated_client_with_tenant.post(reverse("delete-device-view", args=[999999]))

    assert response.status_code == 400
    assert b"Could not delete device" in response.content


# Failed saves


# Two rows with the same name make the interface sync fail, which triggers the error re-render.
@pytest.mark.django_db
def test_failed_update_rerenders_modal_with_submitted_data(
    authenticated_client, authenticated_user_and_tenant_id, device_with_interfaces
):
    user, tenant_id = authenticated_user_and_tenant_id
    tag = create_tag(actor=user, tenant_id=tenant_id, name="Test_Tag_Kept", description="")
    eth0 = Interface.objects.get(device=device_with_interfaces, name="eth0")
    draft = json.dumps([{"id": eth0.id, "name": "eth0"}, {"id": None, "name": "eth0"}])

    response = post_device_update(
        authenticated_client, device_with_interfaces, name="Renamed device", tag_ids=[tag.id], interface_fields=draft
    )

    assert response.status_code == 400
    assert b"Could not update device" in response.content
    object_data = response.context["object_data"]
    assert object_data["id"] == device_with_interfaces.id
    assert object_data["name"] == "Renamed device"
    assert [interface["name"] for interface in object_data["interfaces"]] == ["eth0", "eth0"]
    assert response.context["interface_fields_draft"] == draft
    assert [object_tag.id for object_tag in response.context["object_tags"]] == [tag.id]
    # Manage interfaces must keep pointing at this device, not at the new-device draft modal.
    assert reverse("device-interfaces-modal", args=[device_with_interfaces.id]).encode() in response.content


@pytest.mark.django_db
def test_sync_device_interfaces_clears_vrf(authenticated_user_and_tenant_id, device_with_interfaces):
    user, tenant_id = authenticated_user_and_tenant_id
    eth0 = Interface.objects.get(device=device_with_interfaces, name="eth0")
    eth0.VRF = "mgmt"
    eth0.save()
    eth1 = Interface.objects.get(device=device_with_interfaces, name="eth1")

    sync_device_interfaces(
        actor=user,
        tenant_id=tenant_id,
        device=device_with_interfaces,
        interface_fields=[InterfaceFields(name="eth0", id=eth0.id, vrf=None), InterfaceFields(name="eth1", id=eth1.id)],
    )

    eth0.refresh_from_db()
    assert not eth0.VRF
