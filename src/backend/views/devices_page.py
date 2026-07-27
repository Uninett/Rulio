from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.views.session import get_tenant_context

from backend.views.search import get_global_search_results
from backend.services.get import get_all_device_groups_and_devices_with_tags_from_tenant
from backend.services.get import get_device_group_members
from backend.services.get import get_all_tags_from_object
from backend.services.get import get_all_interfaces_from_device
from backend.objects.tenant_objects.filter_interface import FilterInterface


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


def build_interface_filters(interface):
    filter_links = (
        FilterInterface.objects.filter(interface_id=interface.id, enable=True)
        .select_related("filter", "interface_direction")
        .order_by("policy_sequence")
    )

    ingoing = []
    outgoing = []

    print(
        "RAW FILTER LINKS FOR INTERFACE",
        interface.id,
        list(
            filter_links.values(
                "id",
                "interface_id",
                "filter_id",
                "direction",
                "policy_sequence",
                "enable",
                "interface_direction_id",
            )
        ),
    )

    for link in filter_links:
        direction = (getattr(link.interface_direction, "direction", "") or "").strip().lower()
        filter_obj = link.filter

        filter_obj = link.filter

        item = {
            "id": getattr(filter_obj, "id", None),
            "name": getattr(filter_obj, "name", "") or "",
            "description": getattr(filter_obj, "description", "") or "",
            "policy_sequence": link.policy_sequence,
            "direction": direction,
        }

        if direction == "in":
            ingoing.append(item)
        elif direction == "out":
            outgoing.append(item)

    return {
        "ingoing": ingoing,
        "outgoing": outgoing,
    }


def build_device_interfaces(request, tenant_id, device_id):
    try:
        interfaces = get_all_interfaces_from_device(
            actor=request.user,
            tenant_id=int(tenant_id),
            device_id=device_id,
        )
    except Exception:
        interfaces = []

    interface_list = []

    for interface in interfaces:
        filters = build_interface_filters(interface)

        print("INTERFACE:", interface.id, getattr(interface, "name", ""))
        print("FILTERS:", filters)

        interface_list.append(
            {
                "id": interface.id,
                "row_id": f"interface-{interface.id}",
                "name": getattr(interface, "name", "") or "",
                "description": getattr(interface, "description", "") or "",
                "device_id": getattr(interface, "device_id", None),
                "type": getattr(interface, "type", "") or "",
                "vrf": getattr(interface, "VRF", "") or "",
                "filters": build_interface_filters(interface),
            }
        )

    return interface_list


def build_device_payload(request, tenant_id, device, tag_names=None):
    return {
        "row_id": f"device-{device.id}",
        "name": getattr(device, "name", "") or "",
        "description": getattr(device, "description", "") or "",
        "platform": getattr(device, "platform", "") or "",
        "type": getattr(device, "type", "") or "",
        "tags": tag_names or [],
        "interfaces": build_device_interfaces(
            request=request,
            tenant_id=tenant_id,
            device_id=device.id,
        ),
    }


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
        except Exception:
            device_group_members = []

        group_devices = []

        for member in device_group_members:
            try:
                member_tags = get_all_tags_from_object(
                    actor=request.user,
                    tenant_id=int(tenant_id),
                    object_type="device",
                    object_id=member.id,
                )
                member_tag_names = [tag.name for tag in member_tags]
            except Exception:
                member_tag_names = []

            group_devices.append(
                build_device_payload(
                    request=request,
                    tenant_id=tenant_id,
                    device=member,
                    tag_names=member_tag_names,
                )
            )

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
                        "value": group_devices,
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

        device_payload = build_device_payload(
            request=request,
            tenant_id=tenant_id,
            device=device,
            tag_names=device_tag_names,
        )

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
                    # {
                    #     "label": "Devices",
                    #     "value": [device_payload],
                    #     "modal_on_dblclick": True,
                    # },
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


# def get_devices_view(request):
#     tenant_id = request.session.get("current_tenant_id")
#     if not tenant_id:
#         return {
#             "headers": [],
#             "rows": [],
#         }

#     try:
#         device_groups, devices = get_all_device_groups_and_devices_with_tags_from_tenant(
#             actor=request.user,
#             tenant_id=int(tenant_id),
#         )
#     except Exception:
#         return {
#             "headers": [],
#             "rows": [],
#         }

#     devices = sorted(devices, key=lambda s: (getattr(s, "name", "") or "").lower())
#     device_groups = sorted(device_groups, key=lambda g: (getattr(g, "name", "") or "").lower())

#     headers = ["Type", "Name", "Description", "Tag"]

#     rows = []

#     for group in device_groups:
#         try:
#             device_group_tags = group.get_tags()

#             device_group_tag_names = [tag.name for tag in device_group_tags]
#         except Exception:
#             device_group_tag_names = []

#         try:
#             device_group_members = get_device_group_members(
#                 actor=request.user,
#                 tenant_id=int(tenant_id),
#                 device_group_id=group.id,
#             )
#             print(
#                 "device_group_members:",
#                 list(device_group_members.values("id", "name", "platform", "type", "description")),
#             )
#         except Exception:
#             device_group_members = []

#         rows.append(
#             {
#                 "id": f"devicegroup-{group.id}",
#                 "is_group": True,
#                 "cells": [
#                     "Group",
#                     getattr(group, "name", ""),
#                     getattr(group, "description", ""),
#                     device_group_tag_names,
#                 ],
#                 "expand": [
#                     {
#                         "label": "Devices",
#                         "value": [
#                             {
#                                 "row_id": f"device-{member.id}",
#                                 "name": getattr(member, "name", "") or "",
#                                 "description": getattr(member, "description", "") or "",
#                                 "platform": getattr(member, "platform", "") or "",
#                                 "type": getattr(member, "type", "") or "",
#                                 "tags": getattr(member, "tags", "") or "",
#                                 "interfaces": [
#                                     {
#                                         "id": interface.id,
#                                         "name": interface.name,
#                                         "description": interface.description,
#                                         "device_id": interface.device_id,
#                                         "type": interface.type,
#                                         "VRF": interface.VRF,
#                                     }
#                                     for interface in get_all_interfaces_from_device(
#                                         actor=request.user,
#                                         tenant_id=int(tenant_id),
#                                         device_id=member.id,
#                                     )
#                                 ],
#                             }
#                             for member in device_group_members
#                         ],
#                         "modal_on_dblclick": True,
#                     },
#                     {
#                         "label": "Tags",
#                         "value": device_group_tag_names,
#                     },
#                 ],
#             }
#         )

#     for device in devices:
#         try:
#             devices_tags = get_all_tags_from_object(
#                 actor=request.user,
#                 tenant_id=int(tenant_id),
#                 object_type="device",
#                 object_id=device.id,
#             )
#             device_tag_names = [tag.name for tag in devices_tags]
#         except Exception:
#             device_tag_names = []

#         rows.append(
#             {
#                 "id": f"device-{device.id}",
#                 "is_group": False,
#                 "cells": [
#                     "Device",
#                     getattr(device, "name", ""),
#                     getattr(device, "description", ""),
#                     device_tag_names,
#                 ],
#                 "expand": [
#                     {
#                         "label": "Name",
#                         "value": getattr(device, "name", "") or "",
#                     },
#                     {
#                         "label": "Platform",
#                         "value": getattr(device, "platform", "") or "",
#                     },
#                     {
#                         "label": "Type",
#                         "value": getattr(device, "type", "") or "",
#                     },
#                     {
#                         "label": "Tags",
#                         "value": device_tag_names,
#                     },
#                 ],
#             }
#         )
#     return {
#         "headers": headers,
#         "rows": rows,
#     }
