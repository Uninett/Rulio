from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.services.get import get_all_tags_from_object
from backend.utils.logger import set_up_logger

from backend.views.objects_helpers import get_objects_toolbar_context

from backend.services.attribute_objects.create_attribute_objects import (
    create_address,
)

from backend.services.attribute_objects.get_address_objects import (
    get_address_group_members,
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
    request.session["objects_active_tool"] = "addresses"
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


def build_member_hover_text(member):
    parts = []

    ipv4_network = getattr(member, "ipv4Network", None)
    ipv6_network = getattr(member, "ipv6Network", None)

    ipv4_start = getattr(member, "ipv4Address_start", None)
    ipv4_end = getattr(member, "ipv4Address_end", None)

    ipv6_start = getattr(member, "ipv6Address_start", None)
    ipv6_end = getattr(member, "ipv6Address_end", None)

    if ipv4_network:
        parts.append(f"IPv4: {ipv4_network}")

    if ipv6_network:
        parts.append(f"IPv6: {ipv6_network}")

    if ipv4_start and ipv4_end:
        parts.append(f"IPv4 Range: {ipv4_start} - {ipv4_end}")

    if ipv6_start and ipv6_end:
        parts.append(f"IPv6 Range: {ipv6_start} - {ipv6_end}")

    return " | ".join(parts)


def build_IPv4_row_text(member):
    ipv4_network = getattr(member, "ipv4Network", None)
    ipv4_start = getattr(member, "ipv4Address_start", None)
    ipv4_end = getattr(member, "ipv4Address_end", None)

    if ipv4_network:
        return f"{ipv4_network}"
    elif ipv4_start and ipv4_end:
        return f"{ipv4_start} - {ipv4_end}"
    else:
        return ""


def build_IPv6_row_text(member):
    ipv6_network = getattr(member, "ipv6Network", None)
    ipv6_start = getattr(member, "ipv6Address_start", None)
    ipv6_end = getattr(member, "ipv6Address_end", None)

    if ipv6_network:
        return f"{ipv6_network}"
    elif ipv6_start and ipv6_end:
        return f"{ipv6_start} - {ipv6_end}"
    else:
        return ""


# Fetch addresses from backend and map them to data.
def get_addresses_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    tenant_id = int(tenant_id)

    try:
        _, addresses, address_groups = get_all_addresses_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
            include_global_tenant=True,
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    # Sort the addresses, the key can be dependent on a switch case to allow for different sorting methods in the future.
    addresses = sorted(addresses, key=lambda a: (getattr(a, "name", "") or "").lower())
    address_groups = sorted(address_groups, key=lambda g: (getattr(g, "name", "") or "").lower())

    headers = ["Type", "Name", "Description", "IPv4", "IPv6", "Tags"]
    rows = []

    for address_group in address_groups:
        try:
            address_group_tags = get_all_tags_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_type="addressgroup",
                object_id=address_group.id,
            )
            address_group_tag_names = [tag.name for tag in address_group_tags]
        except Exception:
            address_group_tag_names = []

        try:
            address_group_members = get_address_group_members(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=address_group.id,
            )
        except Exception:
            address_group_members = []

        rows.append(
            {
                "id": f"addressgroup-{address_group.id}",
                "is_group": True,
                "cells": [
                    "Group",
                    getattr(address_group, "name", "") or "",
                    getattr(address_group, "description", "") or "",
                    "",
                    "",
                    address_group_tag_names,
                ],
                "expand": [
                    {
                        "label": "Addresses",
                        "value": [
                            {
                                "row_id": f"address-{member.id}",
                                "name": getattr(member, "name", "") or "",
                                "hover_text": build_member_hover_text(member),
                            }
                            for member in address_group_members
                        ],
                        "modal_on_dblclick": True,
                    },
                    {
                        "label": "Tags",
                        "value": address_group_tag_names,
                    },
                ],
            }
        )

    for address in addresses:
        try:
            address_tags = get_all_tags_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_type="address",
                object_id=address.id,
            )
            tag_names = [tag.name for tag in address_tags]
        except Exception:
            tag_names = []

        expand = []

        field_map = [
            ("IPv4 Type", "ipv4_type"),
            ("IPv6 Type", "ipv6_type"),
            ("IPv4 Network", "ipv4Network"),
            ("IPv6 Network", "ipv6Network"),
            ("IPv4 Start", "ipv4Address_start"),
            ("IPv4 End", "ipv4Address_end"),
            ("IPv6 Start", "ipv6Address_start"),
            ("IPv6 End", "ipv6Address_end"),
        ]

        for label, attr in field_map:
            value = getattr(address, attr, None)
            if value:
                expand.append({"label": label, "value": value})

        if tag_names:
            expand.append({"label": "Tags", "value": tag_names})

        rows.append(
            {
                "id": f"address-{address.id}",
                "is_group": False,
                "cells": [
                    getattr(address, "addr_type", "") or "",
                    getattr(address, "name", "") or "",
                    getattr(address, "description", "") or "",
                    build_IPv4_row_text(address),
                    build_IPv6_row_text(address),
                    tag_names,
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

    object_data = {
        "name": name,
        "description": description,
        "addr_type": addr_type,
        "ipv4_input": ipv4_input,
        "ipv6_input": ipv6_input,
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
                "error_message": "At least one of IPv4 or IPv6 must be selected.",
            },
        )

    try:
        update_address(
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
