from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger

from backend.views.objects_helpers import get_objects_toolbar_context
from backend.views.modal import get_group_options_view

from backend.objects.attributes.address_group_member import AddressGroupMember

from backend.services.attribute_objects.create_attribute_objects import (
    create_address,
)

from backend.services.membership import (
    add_address_to_group,
)

from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)

from backend.services.update import (
    update_address,
)

from backend.services.delete import (
    delete_address,
)

logger = set_up_logger(__name__)


"""
====================================================================
Objects Page: Address
====================================================================
"""


# Render the Addresses tab content for the Objects page.
@login_required(login_url="login")
def get_objects_addresses(request):
    request.session["active_page"] = "objects"
    object_type = "addresses"
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Addresses",
            "object_type": object_type,
            "addresses": get_addresses_view(request),  # Address data for the page
            **get_objects_toolbar_context(
                "addresses", add_button_label="Add Address"
            ),  # Render the Objects page with Addresses as the active tab.
        },
    )


# Fetch addresses from backend and map them to data.
def get_addresses_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        addresses, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
            include_global_tenant=False,
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "IPv4", "IPv6", "Tags"]

    rows = []

    for item in addresses:
        item_type = item.get("type", "")
        is_group = item_type == "AddressGroup"

        tags_value = [tag.get("name", "") for tag in item.get("tags", [])]
        addresses_value = [address.get("name", "") for address in item.get("addresses", [])]

        if is_group:
            expand = [
                {"label": "Addresses", "value": addresses_value},
                {"label": "Tags", "value": tags_value},
            ]
        else:
            expand = [
                {"label": "IPv4 Type", "value": item.get("ipv4_type", "")},
                {"label": "IPv6 Type", "value": item.get("ipv6_type", "")},
                {"label": "IPv4 Start", "value": item.get("ipv4Address_start", "")},
                {"label": "IPv4 End", "value": item.get("ipv4Address_end", "")},
                {"label": "IPv6 Start", "value": item.get("ipv6Address_start", "")},
                {"label": "IPv6 End", "value": item.get("ipv6Address_end", "")},
                {"label": "Tags", "value": tags_value},
            ]

        rows.append(
            {
                "id": f"{item.get('type', '').lower()}-{item.get('id')}",
                "is_group": is_group,
                "cells": [
                    "Group" if item.get("type") == "AddressGroup" else item.get("type", ""),
                    item.get("name", ""),
                    item.get("description", ""),
                    item.get("ipv4Network") or "",
                    item.get("ipv6Network") or "",
                    tags_value,
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


# Parse the IP input value and return a dictionary with the parsed data.
def parse_ip_input(value, update=False):
    value = (value or "").strip()

    if not value:
        return {
            "type": "remove" if update else None,
            "network": None,
            "start": None,
            "end": None,
        }

    if "-" in value:
        start, end = [part.strip() for part in value.split("-", 1)]
        return {
            "type": "custom_range",
            "network": None,
            "start": start or None,
            "end": end or None,
        }

    return {
        "type": "standard",
        "network": value,
        "start": None,
        "end": None,
    }


# Build the IP input value based on the provided type and values.
def build_ip_input(ip_type, network, start, end):
    if ip_type == "standard":
        return network or ""
    if ip_type == "custom_range":
        if start and end:
            return f"{start}-{end}"
    return ""


"""
====================================================================
Objects Page: Address Item
====================================================================
"""


# Handles creation of a new address from modal form submission.
@login_required(login_url="login")
def post_address_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    addr_type = request.POST.get("addr_type", "host")
    ipv4_input = request.POST.get("ipv4_input", "")
    ipv6_input = request.POST.get("ipv6_input", "")

    ipv4_parsed = parse_ip_input(ipv4_input)
    ipv6_parsed = parse_ip_input(ipv6_input)

    ipv4_type = ipv4_parsed["type"]
    ipv6_type = ipv6_parsed["type"]
    ipv4Network = ipv4_parsed["network"]
    ipv6Network = ipv6_parsed["network"]
    ipv4Address_start = ipv4_parsed["start"]
    ipv4Address_end = ipv4_parsed["end"]
    ipv6Address_start = ipv6_parsed["start"]
    ipv6Address_end = ipv6_parsed["end"]
    group_ids = [int(group_id) for group_id in request.POST.getlist("group_ids") if group_id]

    if not ipv4_type and not ipv6_type:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "addresses",
                "modal_content_partial": "partials/modals/_address_form.html",
                "modal_supports_types": True,
                "modal_type": "item",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Address",
                    "group": "Group",
                },
                "object_data": {
                    "name": name,
                    "description": description,
                    "addr_type": addr_type,
                    "ipv4_input": ipv4_input,
                    "ipv6_input": ipv6_input,
                },
                "error_message": "At least one of IPv4 or IPv6 must be selected.",
                "group_options": get_group_options_view(request, "addresses"),
            },
            status=400,
        )

    try:
        created_address = create_address(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
            addr_type=addr_type,
            ipv4_type=ipv4_type,
            ipv6_type=ipv6_type,
            ipv4Network=ipv4Network,
            ipv6Network=ipv6Network,
            ipv4Address_start=ipv4Address_start,
            ipv4Address_end=ipv4Address_end,
            ipv6Address_start=ipv6Address_start,
            ipv6Address_end=ipv6Address_end,
        )

        for group_id in group_ids:
            add_address_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=group_id,
                address_id=created_address.id,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "addresses",
                "modal_content_partial": "partials/modals/_address_form.html",
                "modal_supports_types": True,
                "modal_type": "item",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Address",
                    "group": "Group",
                },
                "error_message": f"Could not create address: {e}",
                "group_options": get_group_options_view(request, "addresses"),
            },
            status=400,
        )

    row = {
        "id": f"address-{created_address.id}",
        "cells": [
            created_address.addr_type or "",
            created_address.name,
            created_address.description,
            created_address.ipv4Network or "-",
            created_address.ipv6Network or "-",
            [],
        ],
        "expand": [
            created_address.ipv4_type or "",
            created_address.ipv6_type or "",
            created_address.ipv4Address_start or "",
            created_address.ipv4Address_end or "",
            created_address.ipv6Address_start or "",
            created_address.ipv6Address_end or "",
            [],
            [],
        ],
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Handles updating an existing address from modal form submission.
@login_required(login_url="login")
def update_address_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    addr_type = request.POST.get("addr_type") or None
    ipv4_input = request.POST.get("ipv4_input", "")
    ipv6_input = request.POST.get("ipv6_input", "")

    ipv4_parsed = parse_ip_input(ipv4_input, update=True)
    ipv6_parsed = parse_ip_input(ipv6_input, update=True)

    ipv4_type = ipv4_parsed["type"]
    ipv6_type = ipv6_parsed["type"]
    ipv4Network = ipv4_parsed["network"]
    ipv6Network = ipv6_parsed["network"]
    ipv4Address_start = ipv4_parsed["start"]
    ipv4Address_end = ipv4_parsed["end"]
    ipv6Address_start = ipv6_parsed["start"]
    ipv6Address_end = ipv6_parsed["end"]

    if ipv4_type == "standard":
        ipv4Address_start = ""
        ipv4Address_end = ""
    elif ipv4_type == "custom_range":
        ipv4Network = ""

    if ipv6_type == "standard":
        ipv6Address_start = ""
        ipv6Address_end = ""
    elif ipv6_type == "custom_range":
        ipv6Network = ""

    group_ids = [int(group_id) for group_id in request.POST.getlist("group_ids") if group_id]

    object_data = {
        "name": name,
        "description": description,
        "addr_type": addr_type,
        "ipv4_input": ipv4_input,
        "ipv6_input": ipv6_input,
        "address_groups": [{"id": group_id} for group_id in group_ids],
    }

    if not ipv4_input.strip() and not ipv6_input.strip():
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Address",
                "modal_mode": "update",
                "modal_row_id": f"address-{object_id}",
                "modal_object_type": "addresses",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_address_form.html",
                "modal_post_url": reverse("update-address-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": "prepareAddressForm",
                "modal_refresh_url": reverse("objects-addresses"),
                "object_data": object_data,
                "group_options": get_group_options_view(request, "addresses"),
                "selected_group_ids": group_ids,
                "error_message": "At least one of IPv4 or IPv6 must be selected.",
            },
        )

    try:
        updated_address = update_address(
            actor=request.user,
            tenant_id=tenant_id,
            address_id=object_id,
            name=name,
            description=description,
            addr_type=addr_type,
            ipv4_type=ipv4_type,
            ipv6_type=ipv6_type,
            ipv4Network=ipv4Network,
            ipv6Network=ipv6Network,
            ipv4Address_start=ipv4Address_start,
            ipv4Address_end=ipv4Address_end,
            ipv6Address_start=ipv6Address_start,
            ipv6Address_end=ipv6Address_end,
        )

        AddressGroupMember.objects.filter(address_id=updated_address.id).delete()

        for group_id in group_ids:
            add_address_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=group_id,
                address_id=updated_address.id,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Address",
                "modal_mode": "update",
                "modal_row_id": f"address-{object_id}",
                "modal_object_type": "addresses",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_address_form.html",
                "modal_post_url": reverse("update-address-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": "prepareAddressForm",
                "modal_refresh_url": reverse("objects-addresses"),
                "object_data": object_data,
                "group_options": get_group_options_view(request, "addresses"),
                "selected_group_ids": group_ids,
                "error_message": f"Could not update address: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of an address from the backend.
@login_required(login_url="login")
def delete_address_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_address(
            actor=request.user,
            tenant_id=tenant_id,
            address_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete address: {e}", status=400)

    return HttpResponse(status=204)
