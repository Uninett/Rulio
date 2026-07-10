from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.views.session import get_tenant_context

from backend.views.search import get_global_search_results
from backend.services.get import get_all_device_groups_and_devices_with_tags_from_tenant
from backend.services.get import get_device_group_members
from backend.services.get import get_all_tags_from_object
from backend.services.get import get_all_interfaces_from_device


"""
====================================================================
Device Page
====================================================================
"""


@login_required(login_url="login")
def get_devices_page(request):
    request.session["active_page"] = "devices"
    return render(
        request,
        "devices.html",
        {
            "active_page": "devices",
            "page_title": "Devices",
            "object_type": "devices",
            "add_button_label": "Add Device",
            "devices": get_devices_view(request),
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )


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

    devices = sorted(devices, key=lambda s: (getattr(s, "name", "") or "").lower())
    device_groups = sorted(device_groups, key=lambda g: (getattr(g, "name", "") or "").lower())

    headers = ["Type", "Name", "Description", "Tag"]

    rows = []

    for group in device_groups:
        try:
            device_group_tags = group.get_tags()

            device_group_tag_names = [tag.name for tag in device_group_tags]
        except Exception:
            device_group_tag_names = []

        try:
            device_group_members = get_device_group_members(
                actor=request.user,
                tenant_id=int(tenant_id),
                device_group_id=group.id,
            )
            print(
                "device_group_members:",
                list(device_group_members.values("id", "name", "platform", "type", "description")),
            )
        except Exception:
            device_group_members = []

        rows.append(
            {
                "id": f"devicegroup-{group.id}",
                "is_group": True,
                "cells": [
                    "Group",
                    getattr(group, "name", ""),
                    getattr(group, "description", ""),
                    device_group_tag_names,
                ],
                "expand": [
                    {
                        "label": "Devices",
                        "value": [
                            {
                                "row_id": f"device-{member.id}",
                                "name": getattr(member, "name", "") or "",
                                "description": getattr(member, "description", "") or "",
                                "platform": getattr(member, "platform", "") or "",
                                "type": getattr(member, "type", "") or "",
                                "tags": getattr(member, "tags", "") or "",
                                "interfaces": [
                                    {
                                        "id": interface.id,
                                        "name": interface.name,
                                        "description": interface.description,
                                        "device_id": interface.device_id,
                                        "type": interface.type,
                                        "VRF": interface.VRF,
                                    }
                                    for interface in get_all_interfaces_from_device(
                                        actor=request.user,
                                        tenant_id=int(tenant_id),
                                        device_id=member.id,
                                    )
                                ],
                            }
                            for member in device_group_members
                        ],
                        "modal_on_dblclick": True,
                    },
                    {
                        "label": "Tags",
                        "value": device_group_tag_names,
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
            device_tag_names = [tag.name for tag in devices_tags]
        except Exception:
            device_tag_names = []

        rows.append(
            {
                "id": f"device-{device.id}",
                "is_group": False,
                "cells": [
                    "Device",
                    getattr(device, "name", ""),
                    getattr(device, "description", ""),
                    device_tag_names,
                ],
                "expand": [
                    {
                        "label": "Name",
                        "value": getattr(device, "name", "") or "",
                    },
                    {
                        "label": "Platform",
                        "value": getattr(device, "platform", "") or "",
                    },
                    {
                        "label": "Type",
                        "value": getattr(device, "type", "") or "",
                    },
                    {
                        "label": "Tags",
                        "value": device_tag_names,
                    },
                ],
            }
        )
    return {
        "headers": headers,
        "rows": rows,
    }
