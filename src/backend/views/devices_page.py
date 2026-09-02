from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from backend.objects.attributes.tag import Tag

from backend.services.delete import delete_device, remove_tag_from_object
from backend.services.get import (
    get_all_device_groups_and_devices_with_tags_from_tenant,
    get_all_interfaces_from_device,
    get_all_tags_from_object,
    get_device_group_members,
    get_object_by_type_and_id,
)
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.membership import add_tag_to_object
from backend.services.tenant_objects.create_tenant_objects import (
    create_device,
)
from backend.services.update import update_device
from backend.utils.logger import set_up_logger
from backend.views.modal import get_group_options_view
from backend.views.search import get_global_search_results
from backend.views.session import get_tenant_context
from constants import GLOBAL_TENANT_ID

logger = set_up_logger(__name__)

"""
====================================================================
Device Page
====================================================================
"""


@login_required(login_url="login")
def get_devices_page(request):
    request.session["active_page"] = "devices"

    context = {
        "active_page": "devices",
        "page_title": "Devices",
        "title": "Devices",
        "object_type": "devices",
        "add_button_label": "Add Device",
        "devices": get_devices_view(request),
        "search_results": get_global_search_results(request),
        **get_tenant_context(request),
    }

    # Used when the modal refreshes #devices-content.
    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/_page_content.html", context)

    # Used for a normal full-page request.
    return render(request, "devices.html", context)


def get_devices_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        device_groups, devices = get_all_device_groups_and_devices_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    devices = sorted(devices, key=lambda d: (getattr(d, "name", "") or "").lower())
    device_groups = sorted(device_groups, key=lambda g: (getattr(g, "name", "") or "").lower())

    headers = ["Type", "Name", "Description", "Platform", "Tags", ""]
    rows = []

    for group in device_groups:
        try:
            device_group_tags = get_all_tags_from_object(
                actor=request.user,
                tenant_id=int(tenant_id),
                object_type="devicegroup",
                object_id=group.id,
            )
        except Exception:
            device_group_tags = []

        try:
            device_group_members = get_device_group_members(
                actor=request.user,
                tenant_id=int(tenant_id),
                device_group_id=group.id,
            )
            logger.info(device_group_members)
        except Exception:
            device_group_members = []

        devices_in_group = []

        member_tag_names = []
        for member in device_group_members:
            devices_in_group.append(
                {
                    "row_id": f"device-{member.id}",
                    "name": getattr(member, "name", "").upper or "",
                    # "description": getattr(member, "description", "") or "",
                }
            )

        logger.info("DEVICES IN GROUP%s", devices_in_group)
        logger.info("member_tag_names%s", member_tag_names)

        rows.append(
            {
                "id": f"devicegroup-{group.id}",
                "is_group": True,
                "tenant_id": group.tenant_id,
                "is_global": group.tenant_id == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, group.tenant_id),
                "cells": [
                    "Group",
                    getattr(group, "name", ""),
                    getattr(group, "description", ""),
                    getattr(group, "platform", ""),
                    device_group_tags,
                ],
                "expand": [
                    {
                        "label": "Devices",
                        "value": devices_in_group,
                        "modal_on_dblclick": True,
                    },
                    {
                        "label": "Tags",
                        "value": device_group_tags,
                    },
                ],
            }
        )
    for device in devices:
        try:
            devices_tags = get_all_tags_from_object(
                actor=request.user,
                tenant_id=int(tenant_id),
                object_type="device",
                object_id=device.id,
            )
        except Exception:
            devices_tags = []

        interfaces_from_device = get_all_interfaces_from_device(
            actor=request.user,
            tenant_id=int(tenant_id),
            device_id=device.id,
        )

        interfaces_for_device = []

        for interface in interfaces_from_device:
            interface_name = getattr(interface, "name", "") or ""
            interfaces_for_device.append(
                [
                    {
                        "value": interface_name,
                        "url": reverse(
                            "interface-filters-view",
                            kwargs={
                                "device_id": device.id,
                                "interface_id": interface.id,
                                # "interface_name": interface_name,
                                # "device_name": device.name,
                                # "interface_name": interface.name,
                            },
                        ),
                    },
                    # getattr(interface, "name", "") or "",
                    getattr(interface, "type", "") or "",
                    getattr(interface, "VRF", "") or "",
                    getattr(interface, "description", "") or "",
                ]
            )

        rows.append(
            {
                "id": f"device-{device.id}",
                "is_group": False,
                "tenant_id": device.tenant_id,
                "is_global": device.tenant_id == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, device.tenant_id),
                "cells": [
                    getattr(device, "type", ""),
                    getattr(device, "name", ""),
                    getattr(device, "description", ""),
                    getattr(device, "platform", ""),
                    devices_tags,
                ],
                "expand": [
                    {
                        "label": "Tags",
                        "value": devices_tags,
                    },
                    {
                        "label": "Interfaces",
                        "headers": ["Interface Name", "Type", "VRF", "Description"],
                        "value": interfaces_for_device,
                        # "value": get_all_interfaces_from_device(request, tenant_id, device),
                    },
                ],
            }
        )
        logger.debug("THESE ARE THE ROWS%s", rows)

    return {
        "headers": headers,
        "rows": rows,
    }


# Handles creation of a new device from modal form submission.
@login_required(login_url="login")
def post_device_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    platform = request.POST.get("platform", "")
    type = request.POST.get("type", "")

    try:
        created_device = create_device(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
            platform=platform,
            type=type,
        )

        submitted_tag_ids = [int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id]

        for tag_id in submitted_tag_ids:
            tag = Tag.objects.get(id=tag_id)
            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=created_device,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "devices",
                "modal_content_partial": "partials/modals/_device_form.html",
                "modal_supports_types": True,
                "modal_type": "item",
                "item_type_editable": False,
                "modal_type_labels": {
                    "item": "Device",
                    "group": "Group",
                },
                "error_message": f"Could not create device: {e}",
            },
            status=400,
        )

    row = {
        "id": f"device-{created_device.id}",
        "is_group": False,
        "tenant_id": created_device.tenant_id,
        "is_global": created_device.tenant_id == GLOBAL_TENANT_ID,
        "can_write": can_write_tenant(request.user, created_device.tenant_id),
        "cells": [
            created_device.type or "",
            created_device.name or "",
            created_device.description or "",
            created_device.platform or "",
            [],  # Tags
        ],
        "expand": [
            {
                "label": "Tags",
                "value": [],
            },
            {
                "label": "Interfaces",
                "headers": ["Interface Name", "Type", "VRF", "Description"],
                "value": [],
            },
        ],
    }

    return render(
        request,
        "partials/objects/_tableRow.html",
        {
            "row": row,
            "headers": ["Type", "Name", "Description", "Platform", "Tags", ""],
            "object_type": "devices",
        },
    )

@login_required(login_url="login")
def update_device_view(request, object_id):
    tenant_id = (
        int(request.session.get("current_tenant_id"))
        if request.session.get("current_tenant_id")
        else None
    )

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    platform = request.POST.get("platform", "")
    device_type = request.POST.get("type", "")

    object_data = {
        "name": name,
        "description": description,
        "platform": platform,
        "type": device_type,
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Device",
                "modal_mode": "update",
                "modal_row_id": f"device-{object_id}",
                "modal_object_type": "devices",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_device_form.html",
                "modal_post_url": reverse("update-device-view", args=[object_id]),
                "modal_delete_url": reverse("delete-device-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("devices"),
                "modal_refresh_target": "#devices-content",
                "object_data": object_data,
                "group_options": get_group_options_view(request, "devices"),
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_device(
            actor=request.user,
            tenant_id=tenant_id,
            device_id=object_id,
            name=name,
            description=description,
            platform=platform,
            type=device_type,
        )

        submitted_tag_ids = {
            int(tag_id)
            for tag_id in request.POST.getlist("tag_ids")
            if tag_id
        }

        current_tags = get_all_tags_from_object(
            actor=request.user,
            tenant_id=tenant_id,
            object_id=object_id,
            object_type="device",
        )
        current_tag_ids = {tag.id for tag in current_tags}

        tag_ids_to_add = submitted_tag_ids - current_tag_ids
        tag_ids_to_remove = current_tag_ids - submitted_tag_ids

        device = get_object_by_type_and_id(
            actor=request.user,
            tenant_id=tenant_id,
            object_type="device",
            object_id=object_id,
        )

        for tag_id in tag_ids_to_add:
            tag = Tag.objects.get(id=tag_id)

            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=device,
            )

        for tag_id in tag_ids_to_remove:
            remove_tag_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_id=object_id,
                object_type="device",
                tag_id=tag_id,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Device",
                "modal_mode": "update",
                "modal_row_id": f"device-{object_id}",
                "modal_object_type": "devices",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_device_form.html",
                "modal_post_url": reverse("update-device-view", args=[object_id]),
                "modal_delete_url": reverse("delete-device-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("devices"),
                "modal_refresh_target": "#devices-content",
                "object_data": object_data,
                "group_options": get_group_options_view(request, "devices"),
                "error_message": f"Could not update device: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


@login_required(login_url="login")
def delete_device_view(request, object_id):
    tenant_id = (
        int(request.session.get("current_tenant_id"))
        if request.session.get("current_tenant_id")
        else None
    )

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_device(
            actor=request.user,
            tenant_id=tenant_id,
            device_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete device: {e}", status=400)

    return HttpResponse(status=204)