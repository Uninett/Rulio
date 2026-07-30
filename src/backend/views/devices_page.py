from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.utils.logger import set_up_logger
from backend.views.session import get_tenant_context

from backend.views.search import get_global_search_results
from backend.services.get import get_all_device_groups_and_devices_with_tags_from_tenant
from backend.services.get import get_device_group_members
from backend.services.get import get_all_tags_from_object
from constants import GLOBAL_TENANT_ID
from backend.services.helper_user_tenant import can_write_tenant

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
    logger.info("TESTER")
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

    headers = ["Type", "Name", "Description", "Tags"]
    rows = []

    for group in device_groups:
        logger.info(group.name)
        try:
            device_group_tags = group.get_tags()
            device_group_tag_names = [tag.name for tag in device_group_tags]
            logger.info(device_group_tags)
        except Exception:
            device_group_tag_names = []

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

            devices_in_group.append(
                {
                    "row_id": f"device-{member.id}",
                    "name": getattr(member, "name", "") or "",
                    "description": getattr(member, "description", "") or "",
                }
            )

        logger.info(f"DEVICES IN GROUP{devices_in_group}")
        logger.info(f"member_tag_names{member_tag_names}")

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
                    device_group_tag_names,
                ],
                "expand": [
                    {
                        "label": "Devices",
                        "value": devices_in_group,
                        "modal_on_dblclick": True,
                    },
                    {
                        "label": "Tags",
                        "value": device_group_tag_names,
                    },
                ],
            }
        )
    logger.info("UTENFOR")
    for device in devices:
        logger.info("INNI")
        logger.info(devices)
        logger.info(device.name)
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
                "tenant_id": device.tenant_id,
                "is_global": device.tenant_id == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, device.tenant_id),
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
        logger.info(f"THESE ARE THE ROWS{rows}")

    return {
        "headers": headers,
        "rows": rows,
    }


# def build_interface_filters(interface):
#     filter_links = (
#         FilterInterface.objects.filter(interface_id=interface.id, enable=True)
#         .select_related("filter", "interface_direction")
#         .order_by("policy_sequence")
#     )

#     ingoing = []
#     outgoing = []

#     for link in filter_links:
#         direction = (getattr(link.interface_direction, "direction", "") or "").strip().lower()
#         filter_obj = link.filter

#         filter_obj = link.filter

#         item = {
#             "id": getattr(filter_obj, "id", None),
#             "name": getattr(filter_obj, "name", "") or "",
#             "description": getattr(filter_obj, "description", "") or "",
#             "policy_sequence": link.policy_sequence,
#             "direction": direction,
#         }

#         if direction == "in":
#             ingoing.append(item)
#         elif direction == "out":
#             outgoing.append(item)

#     return {
#         "ingoing": ingoing,
#         "outgoing": outgoing,
#     }


# def build_device_interfaces(request, tenant_id, device_id):
#     try:
#         interfaces = get_all_interfaces_from_device(
#             actor=request.user,
#             tenant_id=int(tenant_id),
#             device_id=device_id,
#         )
#     except Exception:
#         interfaces = []

#     interface_list = []

#     for interface in interfaces:
#         filters = build_interface_filters(interface)

#         # logger.info("INTERFACE:", interface.id, getattr(interface, "name", ""))
#         # logger.info("FILTERS:", filters)

#         interface_list.append(
#             {
#                 "id": interface.id,
#                 "row_id": f"interface-{interface.id}",
#                 "name": getattr(interface, "name", "") or "",
#                 "description": getattr(interface, "description", "") or "",
#                 "device_id": getattr(interface, "device_id", None),
#                 "type": getattr(interface, "type", "") or "",
#                 "vrf": getattr(interface, "VRF", "") or "",
#                 "filters": build_interface_filters(interface),
#             }
#         )

#     return interface_list


# # def build_device_payload(request, tenant_id, device, tag_names=None):
# #     return {
# #         "row_id": f"device-{device.id}",
# #         "name": getattr(device, "name", "") or "",
# #         "description": getattr(device, "description", "") or "",
# #         "platform": getattr(device, "platform", "") or "",
# #         "type": getattr(device, "type", "") or "",
# #         "tags": tag_names or [],
# #         "interfaces": build_device_interfaces(
# #             request=request,
# #             tenant_id=tenant_id,
# #             device_id=device.id,
# #         ),
# #     }


# def build_device_table_row(request, tenant_id, device, tag_names=None):
#     tag_names = tag_names or []

#     return {
#         "id": f"device-{device.id}",
#         "is_group": False,
#         "cells": [
#             "Device",
#             getattr(device, "name", "") or "",
#             getattr(device, "description", "") or "",
#             tag_names,
#         ],
#         "expand": [
#             {
#                 "label": "Name",
#                 "value": getattr(device, "name", "") or "",
#             },
#             {
#                 "label": "Platform",
#                 "value": getattr(device, "platform", "") or "",
#             },
#             {
#                 "label": "Type",
#                 "value": getattr(device, "type", "") or "",
#             },
#             {
#                 "label": "Interfaces",
#                 "value": build_device_interfaces(
#                     request=request,
#                     tenant_id=tenant_id,
#                     device_id=device.id,
#                 ),
#                 "modal_on_dblclick": True,
#             },
#             {
#                 "label": "Tags",
#                 "value": tag_names,
#             },
#         ],
#     }
