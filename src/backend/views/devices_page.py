import zipfile
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.services.config_generation.generate_interface_config import (
    generate_interface_config_results,
)
from backend.services.get import (
    get_all_device_groups_and_devices_with_tags_from_tenant,
    get_all_filters_from_interface,
    get_all_interfaces_from_device,
    get_all_tags_from_object,
    get_device_group_members,
    get_object_by_type_and_id,
)
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.membership import add_filter_to_interface, add_tag_to_object
from backend.services.tenant_objects.create_tenant_objects import (
    create_device,
)
from backend.utils.logger import set_up_logger
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


def _sanitize_zip_name(name: str, *, fallback: str) -> str:
    if not isinstance(name, str):
        return fallback

    sanitized = name.strip().replace("\\", "_").replace("/", "_").replace("\r", "").replace("\n", "").replace(" ", "_")
    return sanitized or fallback


def _normalize_generated_config_files(config: object, *, fallback_name: str) -> dict[str, str]:
    if config is None:
        return {}

    if isinstance(config, str):
        return {fallback_name: config}

    items_method = getattr(config, "items", None)
    if callable(items_method):
        normalized: dict[str, str] = {}

        try:
            for filename, content in items_method():
                if not isinstance(filename, str) or not filename.strip():
                    logger.warning("Skipping generated config entry with invalid filename: %r", filename)
                    continue

                if not isinstance(content, str):
                    logger.warning(
                        "Skipping generated config entry for filename %r because content is not a string: %r",
                        filename,
                        type(content),
                    )
                    continue

                safe_filename = _sanitize_zip_name(filename, fallback=fallback_name)
                normalized[safe_filename] = content

            return normalized
        except Exception:
            logger.exception("Failed to normalize generated config files for type %r", type(config))
            return {}

    logger.warning("Unsupported generated config type: %r", type(config))
    return {}


def _extract_single_generated_file(config: object, *, fallback_name: str) -> tuple[str, str] | None:
    files = _normalize_generated_config_files(config, fallback_name=fallback_name)

    if not files:
        return None

    if len(files) > 1:
        raise ValueError(f"Expected at most one generated file, but got {len(files)}: {list(files.keys())}")

    return next(iter(files.items()))


def _get_filename_extension(filename: str, *, fallback: str = ".txt") -> str:
    if not isinstance(filename, str):
        return fallback

    if "." not in filename:
        return fallback

    _, ext = filename.rsplit(".", 1)
    ext = ext.strip()
    return f".{ext}" if ext else fallback


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
            "download_url": (f"/devices/interfaces/{interface_id}/download-config/" if not result.has_errors else None),
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

    first_interface_direction = (
        InterfaceDirection.objects.select_related("interface").filter(interface_id=interface_id).first()
    )
    interface_name = _sanitize_zip_name(
        getattr(first_interface_direction.interface, "name", "") if first_interface_direction else "",
        fallback=f"interface_{interface_id}",
    )
    device_name = (
        Device.objects.filter(id=first_interface_direction.interface.device_id).first().name
        if first_interface_direction
        else ""
    )

    inbound_file = _extract_single_generated_file(
        result.inbound.config,
        fallback_name="config_in.txt",
    )
    outbound_file = _extract_single_generated_file(
        result.outbound.config,
        fallback_name="config_out.txt",
    )

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        if inbound_file:
            original_filename, content = inbound_file
            ext = _get_filename_extension(original_filename, fallback=".txt")
            zip_file.writestr(f"{interface_name}_in{ext}", content)

        if outbound_file:
            original_filename, content = outbound_file
            ext = _get_filename_extension(original_filename, fallback=".txt")
            zip_file.writestr(f"{interface_name}_out{ext}", content)

        if result.has_warnings:
            zip_file.writestr("warnings.txt", "\n".join(result.all_warnings()))

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{device_name}_{interface_name}_configs.zip"'
    return response


# def build_interface_filters(interface):
#     filter_links = (
#         FilterInterface.objects.filter(interface_id=interface.id, enable=True)
#         .select_related("filter", "interface_direction")
#         .order_by("policy_sequence")
#     )
@login_required(login_url="login")
def get_interface_page(request):
    request.session["active_page"] = "interfaces"
    return render(
        request,
        "interface_filters.html",
        {
            "active_page": "interfaces",
            "page_title": "Interfaces",
            "object_type": "interfaces",
            "add_button_label": "Add Filter",
            "interfaces": interface_filters_view(request),
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )


@login_required(login_url="login")
def interface_filters_view(request, device_id, interface_id):
    tenant_id = request.session.get("current_tenant_id")

    if not tenant_id:
        context = {
            "active_page": "interfaces",
            "title": "Interfaces",
            "page_title": "Interfaces",
            "object_type": "interfaces",
            "device": None,
            "interface": None,
            "filters": {"headers": ["Direction", "Filters", ""], "rows": []},
            **get_tenant_context(request),
        }

        if request.headers.get("HX-Request") == "true":
            return render(request, "partials/_page_content.html", context)

        return render(request, "interface_filters.html", context)

    tenant_id = int(tenant_id)
    # headers = ["Filter Name", "Filter Description", "Direction", "Policy Sequence", "Enable", ""]
    # rows_ingoing = []
    # rows_outgoing = []
    headers = ["Direction", "Filters", ""]
    rows = []

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

    for direction in ["in", "out"]:
        filter_objects = get_all_filters_from_interface(
            actor=request.user,
            tenant_id=tenant_id,
            interface_id=selected_interface.id,
            direction=direction,
        )

        filters_for_direction = []

        for filter_object in filter_objects:
            filters_for_direction.append(
                [
                    getattr(filter_object, "name", "") or "",
                    getattr(filter_object, "description", "") or "",
                    "Enabled" if getattr(filter_object, "interface_enable", False) else "Disabled",
                    getattr(filter_object, "policy_sequence", "") or "",
                ]
            )

        direction_label = "Ingoing" if direction == "in" else "Outgoing"

        rows.append(
            {
                "id": f"interface-{selected_interface.id}-{direction}",
                "is_global": device.tenant_id == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, device.tenant_id),
                "cells": [
                    direction_label,
                    len(filters_for_direction),
                ],
                "expand": [
                    {
                        "label": "Filters",
                        "headers": [
                            "Filter Name",
                            "Description",
                            "Enabled",
                            "Sequence",
                            "",
                        ],
                        "value": filters_for_direction,
                        "modal_on_dblclick": True,
                    },
                ],
            }
        )

    page_title = f"{device.name} → {selected_interface.name}"
    context = {
        "active_page": "interfaces",
        "title": page_title,
        "page_title": page_title,
        "object_type": "interfaces",
        "device": device,
        "interface": selected_interface,
        "current_device_id": device.id,
        "current_interface_id": selected_interface.id,
        "add_button_label": "Add filter",
        "search_results": get_global_search_results(request),
        "filters": {
            "headers": headers,
            "rows": rows,
        },
        **get_tenant_context(request),
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/_page_content.html", context)

    return render(request, "interface_filters.html", context)


@login_required(login_url="login")
def post_interface_view(request):
    tenant_id_raw = request.session.get("current_tenant_id")
    interface_id_raw = request.POST.get("interface_id", "").strip()
    enable = request.POST.get("enable") == "on"

    ingoing_filter_ids_raw = request.POST.get("ingoing_filter_ids", "")
    outgoing_filter_ids_raw = request.POST.get("outgoing_filter_ids", "")

    object_data = {
        "interface_id": interface_id_raw,
        "enable": enable,
        "ingoing_filter_ids": [value.strip() for value in ingoing_filter_ids_raw.split(",") if value.strip()],
        "outgoing_filter_ids": [value.strip() for value in outgoing_filter_ids_raw.split(",") if value.strip()],
        "ingoing_filter_names": [],
        "outgoing_filter_names": [],
    }

    def render_form_error(error_message: str, status: int = 400):
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "interfaces",
                "modal_content_partial": "partials/modals/_interface_form.html",
                "modal_supports_types": False,
                "object_data": object_data,
                "error_message": error_message,
            },
            status=status,
        )

    if not tenant_id_raw:
        return render_form_error("Tenant not set.")

    try:
        tenant_id = int(tenant_id_raw)
        interface_id = int(interface_id_raw)
    except (TypeError, ValueError):
        return render_form_error("Invalid tenant or interface id.")

    interface = Interface.objects.filter(id=interface_id, device__tenant_id=tenant_id).first()
    if interface is None:
        return render_form_error("Interface not found.")

    try:
        ingoing_filter_ids = [int(value) for value in ingoing_filter_ids_raw.split(",") if value.strip()]
        outgoing_filter_ids = [int(value) for value in outgoing_filter_ids_raw.split(",") if value.strip()]
    except ValueError:
        return render_form_error("Invalid filter ids.")

    valid_filter_ids = set(
        Filter.objects.filter(
            id__in=set(ingoing_filter_ids + outgoing_filter_ids), tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]
        ).values_list("id", flat=True)
    )

    invalid_ids = [
        filter_id for filter_id in ingoing_filter_ids + outgoing_filter_ids if filter_id not in valid_filter_ids
    ]
    if invalid_ids:
        return render_form_error(
            f"Invalid filter selection: {', '.join(str(value) for value in sorted(set(invalid_ids)))}"
        )

    try:
        with transaction.atomic():
            for sequence, filter_id in enumerate(ingoing_filter_ids, start=1):
                add_filter_to_interface(
                    actor=request.user,
                    tenant_id=tenant_id,
                    filter_id=filter_id,
                    interface_id=interface_id,
                    policy_sequence=sequence,
                    enable=enable,
                    direction="in",
                )

            for sequence, filter_id in enumerate(outgoing_filter_ids, start=1):
                add_filter_to_interface(
                    actor=request.user,
                    tenant_id=tenant_id,
                    filter_id=filter_id,
                    interface_id=interface_id,
                    policy_sequence=sequence,
                    enable=enable,
                    direction="out",
                )

            FilterInterface.objects.filter(
                interface_id=interface_id,
                direction="in",
            ).exclude(filter_id__in=ingoing_filter_ids).delete()

            FilterInterface.objects.filter(
                interface_id=interface_id,
                direction="out",
            ).exclude(filter_id__in=outgoing_filter_ids).delete()

    except Exception as exc:
        return render_form_error(f"Unable to update interface filters: {exc}")

    return HttpResponse(status=204)


@login_required(login_url="login")
def get_interface_filter_selector_modal(request, selector_type: str):
    supported_selector_types = {
        "ingoing_filter",
        "outgoing_filter",
    }

    if selector_type not in supported_selector_types:
        return HttpResponse(f"Unsupported interface selector type: {selector_type!r}", status=400)

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return HttpResponse("No tenant selected.", status=400)

    try:
        tenant_id = int(tenant_id_raw)
    except (TypeError, ValueError):
        return HttpResponse("Invalid tenant selected.", status=400)

    selected_ids_raw = request.GET.get("selected_ids", "")
    selected_object_ids = {value.strip() for value in selected_ids_raw.split(",") if value.strip()}

    filters = Filter.objects.filter(tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).order_by("name")
    item_options = [
        {
            "selector_id": str(filter_obj.id),
            "name": filter_obj.name,
        }
        for filter_obj in filters
    ]

    direction_label = "Ingoing" if selector_type == "ingoing_filter" else "Outgoing"

    context = {
        "modal_title": f"Edit {direction_label} Filters",
        "modal_mode": "submodal",
        "modal_object_type": "rule-selector",
        "modal_content_partial": "partials/modals/_interface_selector_modal.html",
        "modal_instance_id": f"submodal-{selector_type}",
        "modal_is_submodal": True,
        "selector_type": selector_type,
        "object_kind": "filters",
        "selected_object_ids": selected_object_ids,
        "item_options": item_options,
    }

    return render(request, "partials/_modal.html", context)


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
