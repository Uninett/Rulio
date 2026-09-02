from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from backend.objects.attributes.tag import Tag
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.membership import add_devices_to_group, add_tag_to_object
from backend.services.tenant_objects.create_tenant_objects import create_device_group
from backend.utils.logger import set_up_logger
from backend.views.modal import get_item_options_view
from constants import GLOBAL_TENANT_ID

logger = set_up_logger(__name__)


"""
====================================================================
Objects Page: device Group
====================================================================
"""


# Handles creation of a new device group from modal form submission.
@login_required(login_url="login")
def post_device_group_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    device_ids = [int(device_id) for device_id in request.POST.getlist("device_ids") if device_id]

    try:
        created_device_group = create_device_group(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )

        if device_ids:
            add_devices_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                device_group_id=created_device_group.id,
                device_ids=device_ids,
            )

        submitted_tag_ids = [int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id]

        for tag_id in submitted_tag_ids:
            tag = Tag.objects.get(id=tag_id)
            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=created_device_group,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "devices",
                "modal_content_partial": "partials/modals/_device_group_form.html",
                "modal_supports_types": True,
                "modal_type": "group",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "device",
                    "group": "device Group",
                },
                "error_message": f"Could not create device group: {e}",
                "item_options": get_item_options_view(request, "devices"),
            },
            status=400,
        )

    row = {
        "id": f"devicegroup-{created_device_group.id}",
        "is_group": True,
        "tenant_id": created_device_group.tenant_id,
        "is_global": created_device_group.tenant_id == GLOBAL_TENANT_ID,
        "can_write": can_write_tenant(request.user, created_device_group.tenant_id),
        "cells": [
            "Group",
            created_device_group.name or "",
            created_device_group.description or "",
            "",
            [],  # Tags
        ],
        "expand": [
            {
                "label": "Devices",
                "value": [],
                "modal_on_dblclick": True,
            },
            {
                "label": "Tags",
                "value": [],
            },
        ],
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})

@login_required(login_url="login")
def update_device_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    device_ids = [int(device_id) for device_id in request.POST.getlist("device_ids") if device_id]

    object_data = {
        "name": name,
        "description": description,
        "devicees": [{"id": device_id} for device_id in device_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update device Group",
                "modal_mode": "update",
                "modal_row_id": f"devicegroup-{object_id}",
                "modal_object_type": "devicees",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_device_group_form.html",
                "modal_post_url": reverse("update-device-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-devicees"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "devicees"),
                "selected_device_ids": device_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_device_group(
            actor=request.user,
            tenant_id=tenant_id,
            device_group_id=object_id,
            name=name,
            description=description,
        )

        # Read current members from the database
        current_members = get_device_group_members(
            actor=request.user,
            tenant_id=tenant_id,
            device_group_id=object_id,
        )

        current_device_ids = set(
            current_members.values_list("id", flat=True)
        )  # Convert current members to a set of ids
        submitted_device_ids = set(device_ids)  # Convert submitted selected ids to a set

        device_ids_to_remove = current_device_ids - submitted_device_ids  # Find what to remove
        device_ids_to_add = submitted_device_ids - current_device_ids  # Find what to add

        for device_id in device_ids_to_remove:
            remove_device_from_group(
                actor=request.user,
                tenant_id=tenant_id,
                device_group_id=object_id,
                device_id=device_id,
            )

        if device_ids_to_add:
            add_devices_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                device_group_id=object_id,
                device_ids=list(device_ids_to_add),
            )

        submitted_tag_ids = {int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id}

        current_tags = get_all_tags_from_object(
            actor=request.user,
            tenant_id=tenant_id,
            object_id=object_id,
            object_type="devicegroup",
        )
        current_tag_ids = {tag.id for tag in current_tags}

        tag_ids_to_add = submitted_tag_ids - current_tag_ids
        tag_ids_to_remove = current_tag_ids - submitted_tag_ids

        obj = get_object_by_type_and_id(
            actor=request.user,
            tenant_id=tenant_id,
            object_type="devicegroup",
            object_id=object_id,
        )

        for tag_id in tag_ids_to_add:
            tag = Tag.objects.get(id=tag_id)
            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=obj,
            )

        for tag_id in tag_ids_to_remove:
            remove_tag_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_id=object_id,
                object_type="devicegroup",
                tag_id=tag_id,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update device Group",
                "modal_mode": "update",
                "modal_row_id": f"devicegroup-{object_id}",
                "modal_object_type": "devicees",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_device_group_form.html",
                "modal_post_url": reverse("update-device-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-devicees"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "devicees"),
                "selected_device_ids": device_ids,
                "error_message": f"Could not update device group: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)

# Handles deletion of an device group from the backend.
@login_required(login_url="login")
def delete_device_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_device_group(
            actor=request.user,
            tenant_id=tenant_id,
            device_group_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete device group: {e}", status=400)

    return HttpResponse(status=204)
