import zipfile
from io import BytesIO

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from backend.utils.logger import set_up_logger
from backend.views.session import get_tenant_context
from backend.views.search import get_global_search_results
from backend.services.get import (
    get_all_device_groups_and_devices_with_tags_from_tenant,
    get_all_filters_from_interface,
    get_object_by_type_and_id,
)
from backend.services.get import get_device_group_members
from backend.services.get import get_all_tags_from_object
from backend.services.get import get_all_interfaces_from_device
from constants import GLOBAL_TENANT_ID
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.config_generation.generate_interface_config import (
    generate_interface_config_results,
    serialize_generated_config,
)



logger = set_up_logger(__name__)

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

        for member in device_group_members:
            devices_in_group.append(
                {
                    "row_id": f"device-{member.id}",
                    "name": getattr(member, "name", "") or "",
                    # "description": getattr(member, "description", "") or "",
                }
            )

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

    return {
        "headers": headers,
        "rows": rows,
    }


@login_required(login_url="login")
def check_interface_config_generation(request, interface_id):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return JsonResponse(
            {
                "status": "error",
                "errors": ["No tenant selected."],
                "warnings": [],
                "can_download": False,
                "download_url": None,
            },
            status=400,
        )

    try:
        tenant_id = int(tenant_id)
    except (TypeError, ValueError):
        return JsonResponse(
            {
                "status": "error",
                "errors": ["Invalid tenant selected."],
                "warnings": [],
                "can_download": False,
                "download_url": None,
            },
            status=400,
        )

    result = generate_interface_config_results(
        actor=request.user,
        tenant_id=tenant_id,
        interface_id=interface_id,
    )

    return JsonResponse(
        {
            "status": result.status,
            "errors": result.all_errors(),
            "warnings": result.all_warnings(),
            "can_download": not result.has_errors,
            "download_url": (
                f"/devices/interfaces/{interface_id}/download-config/"
                if not result.has_errors
                else None
            ),
        }
    )


@login_required(login_url="login")
def download_interface_configs(request, interface_id):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400, content_type="text/plain")

    try:
        tenant_id = int(tenant_id)
    except (TypeError, ValueError):
        return HttpResponse("Invalid tenant selected.", status=400, content_type="text/plain")

    result = generate_interface_config_results(
        actor=request.user,
        tenant_id=tenant_id,
        interface_id=interface_id,
    )

    if result.has_errors:
        error_lines = result.all_errors()
        if result.has_warnings:
            error_lines.append("")
            error_lines.append("Warnings:")
            error_lines.extend(result.all_warnings())

        return HttpResponse(
            "\n".join(error_lines) or "Failed to generate config.",
            status=400,
            content_type="text/plain",
        )

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("config_in.txt", serialize_generated_config(result.inbound.config))
        zip_file.writestr("config_out.txt", serialize_generated_config(result.outbound.config))

        if result.has_warnings:
            zip_file.writestr("warnings.txt", "\n".join(result.all_warnings()))

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="interface_{interface_id}_configs.zip"'
    return response

# def build_interface_filters(interface):
#     filter_links = (
#         FilterInterface.objects.filter(interface_id=interface.id, enable=True)
#         .select_related("filter", "interface_direction")
#         .order_by("policy_sequence")
#     )


def interface_filters_view(request, device_id, interface_id):
    tenant_id = request.session.get("current_tenant_id")

    if not tenant_id:
        return render(
            request,
            "interface_filters.html",
            {
                "page_title": "Interfaces",
                "device": None,
                "interface": None,
                "filters": [],
            },
        )

    headers = ["Filter Name", "Filter Description", "Direction", "Enable", ""]
    rows = []
    tenant_id = int(tenant_id)

    device = get_object_by_type_and_id(
        actor=request.user,
        tenant_id=tenant_id,
        object_type="device",
        object_id=device_id,
    )
    print(f"Device: {device.name} ({device.id})")

    device_interfaces = get_all_interfaces_from_device(
        actor=request.user,
        tenant_id=tenant_id,
        device_id=device_id,
        # interface_id=interface_id,
    )
    print(f"Device interfaces: {[interface.id for interface in device_interfaces]}")

    selected_interface = next(
        (interface for interface in device_interfaces if interface.id == interface_id),
        None,
    )
    print(f"Selected interface: {selected_interface.name} ({selected_interface.id})")

    filter_objects = get_all_filters_from_interface(
        actor=request.user,
        tenant_id=tenant_id,
        interface_id=selected_interface.id,
    )
    print(f"Filter objects: {[filter_object.name for filter_object in filter_objects]}")

    for filter_object in filter_objects:
        rows.append(
            {
                "id": f"filter-{filter_object.id}",
                "is_global": filter_object.tenant_id == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, device.tenant_id),
                "cells": [
                    getattr(filter_object, "name", "") or "",
                    getattr(filter_object, "description", "") or "",
                    getattr(filter_object, "direction", "") or "",
                    getattr(filter_object, "enable", "") or "",
                ],
            }
        )

    return render(
        request,
        "interface_filters.html",
        {
            "device": device,
            "interface": selected_interface,
            "page_title": f"{device.name} → {selected_interface.name}",
            # "page_title": "Interfaces",
            "object_type": "interfaces",
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
            "filters": {
                "headers": headers,
                "rows": rows,
            },
        },
    )
