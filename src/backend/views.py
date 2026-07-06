from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember

from backend.services.attribute_objects.create_attribute_objects import (
    create_address,
    create_address_group,
    create_service,
    create_service_group,
)

from backend.services.membership import (
    add_address_to_group,
    add_addresses_to_group,
    add_service_to_group,
    add_services_to_group,
)

from backend.services.get import (
    get_all_tags_from_tenant,
    get_all_objects_with_certain_tag,
    get_all_filters_with_tags_from_tenant,
)

from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)

from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)

from backend.services.update import (
    update_address,
    update_service,
    update_address_group,
    update_service_group,
)

from backend.services.delete import (
    delete_address,
    delete_address_group,
    delete_service,
    delete_service_group,
)

logger = set_up_logger(__name__)

"""
====================================================================
Login Page
====================================================================
"""


def get_login_page(request):
    if request.user.is_authenticated:
        return redirect(request.session.get("active_page", "devices"))

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request,
                "login.html",
                {
                    "error": "Invalid username or password",
                },
                status=401,
            )

        login(request, user)
        request.session["active_page"] = "devices"

        if user.is_superuser:
            # Set the first tenant as the current tenant for superusers as default.
            first_tenant = Tenant.objects.first()
            if first_tenant:
                request.session["current_tenant_id"] = first_tenant.id
        else:
            # Set the current tenant for non-superusers based on their membership.
            tenant_member = TenantUserMember.objects.filter(user_id=user.id).first()
            if tenant_member:
                request.session["current_tenant_id"] = tenant_member.tenant_id

        return redirect("devices")

    return render(
        request,
        "login.html",
    )


# Remove the current tenant from the session and log out the user, then redirect to the login page.
@login_required(login_url="login")
def logout_view(request):
    if request.method == "POST":
        request.session.pop("current_tenant_id", None)
        request.session.pop("active_page", None)
        logout(request)
        return redirect("login")

    return redirect("login")


"""
====================================================================
Tenant
====================================================================
"""


# Gets the list of tenants from the backend
def get_tenants_view(request):
    if not request.user.is_superuser:
        return []

    tenants = Tenant.objects.all()

    return [
        {
            "id": tenant.id,
            "name": tenant.tenant_name,
        }
        for tenant in tenants
    ]


# Builds the data that the templates need in order to render the tenant dropdown correctly
def get_tenant_context(request):
    return {
        "tenants": get_tenants_view(request),
        "selected_tenant": request.session.get("current_tenant_id"),
    }


# Handles setting the current tenant in the session based on the selected tenant from the dropdown.
@login_required(login_url="login")
def set_tenant_view(request):
    if request.method != "POST":
        return redirect(request.session.get("active_page", "devices"))

    tenant_id = request.POST.get("tenant_id")

    if not tenant_id:
        return HttpResponse("Missing tenant_id", status=400)

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return HttpResponse(f"Tenant with id {tenant_id} does not exist.", status=404)

    request.session["current_tenant_id"] = tenant.id
    request.session.modified = True

    return HttpResponse(status=204)


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
            **get_tenant_context(request),
        },
    )


"""
====================================================================
Filters Page
====================================================================
"""


@login_required(login_url="login")
def get_filters_page(request):
    request.session["active_page"] = "filters"
    return render(
        request,
        "filters.html",
        {
            "active_page": "filters",
            "page_title": "Filters",
            "object_type": "filters",
            "add_button_label": "Add Filter",
            "filters": get_filters_view(request),  # Address data for the page
            **get_tenant_context(request),
        },
    )


def get_filters_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        results, filters = get_all_filters_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = [
        "Name",
        "Description",
    ]

    rows = []

    for item in results:
        expand = [
            {"label": "Filter Name", "value": item.get("filter_name", "")},
            {"label": "Filter Description", "value": item.get("filter_description", "")},
            {"label": "Direction", "value": item.get("direction", "")},
            {"label": "Enable", "value": item.get("enable", "")},
        ]

        rows.append(
            {
                "id": item.get("filter_id", ""),
                "cells": [
                    item.get("filter_name", ""),
                    item.get("filter_description", ""),
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


"""
====================================================================
Objects Page
====================================================================
"""


@login_required(login_url="login")
def get_objects_page(request):
    request.session["active_page"] = "objects"
    return render(
        request,
        "objects.html",
        {
            "active_page": "objects",
            "page_title": "Addresses",
            "object_type": "addresses",
            **get_objects_toolbar_context("addresses"),  # Render the Objects page with Addresses as the default tab.
            "addresses": get_addresses_view(request),  # Address data for the page
            **get_tenant_context(request),
        },
    )


# Build shared toolbar context for the Objects page tabs.
def get_objects_toolbar_context(active_tool, add_button_label="Add Address"):
    return {
        "active_tool": active_tool,
        "toggle_items": [
            {
                "key": "addresses",
                "label": "Addresses",
                "url": reverse("objects-addresses"),  # URL for loading the Addresses tab content
            },
            {
                "key": "services",
                "label": "Services",
                "url": reverse("objects-services"),  # URL for loading the Service tab content
            },
        ],
        "add_button_label": add_button_label,
    }


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


"""
====================================================================
Objects Page: Address Group
====================================================================
"""


# Handles creation of a new address group from modal form submission.
@login_required(login_url="login")
def post_address_group_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    address_ids = [int(address_id) for address_id in request.POST.getlist("address_ids") if address_id]

    try:
        created_address_group = create_address_group(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )

        if address_ids:
            add_addresses_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=created_address_group.id,
                address_ids=address_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "addresses",
                "modal_content_partial": "partials/modals/_address_group_form.html",
                "modal_supports_types": True,
                "modal_type": "group",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Address",
                    "group": "Address Group",
                },
                "error_message": f"Could not create address group: {e}",
                "item_options": get_item_options_view(request, "addresses"),
            },
            status=400,
        )

    row = {
        "id": f"addressgroup-{created_address_group.id}",
        "cells": [
            "AddressGroup",
            created_address_group.name,
            created_address_group.description,
            "-",
            "-",
            [],
        ],
        "expand": [
            "",
            "",
            "",
            "",
            "",
            "",
            [],
            [],
        ],
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


@login_required(login_url="login")
def update_address_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    address_ids = [int(address_id) for address_id in request.POST.getlist("address_ids") if address_id]

    object_data = {
        "name": name,
        "description": description,
        "addresses": [{"id": address_id} for address_id in address_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Address Group",
                "modal_mode": "update",
                "modal_row_id": f"addressgroup-{object_id}",
                "modal_object_type": "addresses",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_address_group_form.html",
                "modal_post_url": reverse("update-address-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-addresses"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "addresses"),
                "selected_address_ids": address_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_address_group(
            actor=request.user,
            tenant_id=tenant_id,
            address_group_id=object_id,
            name=name,
            description=description,
        )

        AddressGroupMember.objects.filter(group_id=object_id).delete()

        if address_ids:
            add_addresses_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=object_id,
                address_ids=address_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Address Group",
                "modal_mode": "update",
                "modal_row_id": f"addressgroup-{object_id}",
                "modal_object_type": "addresses",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_address_group_form.html",
                "modal_post_url": reverse("update-address-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-addresses"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "addresses"),
                "selected_address_ids": address_ids,
                "error_message": f"Could not update address group: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of an address group from the backend.
@login_required(login_url="login")
def delete_address_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_address_group(
            actor=request.user,
            tenant_id=tenant_id,
            address_group_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete address group: {e}", status=400)

    return HttpResponse(status=204)


"""
====================================================================
Objects Page: Service
====================================================================
"""


# Render the Services tab content for the Objects page.
@login_required(login_url="login")
def get_objects_services(request):
    request.session["active_page"] = "objects"
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Services",
            "object_type": "services",
            "services": get_services_view(request),  # Service data for the page
            **get_objects_toolbar_context(
                "services", add_button_label="Add Service"
            ),  # Render the Objects page with Services as the active tab.
        },
    )


# Fetch services from the backend and map them to data.
def get_services_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        services, _, _ = get_all_services_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
            include_global_tenant=False,
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "Protocol", "Port Start", "Port End", "Tags"]

    rows = []

    for item in services:
        item_type = item.get("type", "")
        is_group = item_type == "ServiceGroup"

        tags_value = [tag.get("name", "") for tag in item.get("tags", [])]
        services_value = [service.get("name", "") for service in item.get("services", [])]

        if is_group:
            expand = [
                {"label": "Services", "value": services_value},
                {"label": "Tags", "value": tags_value},
            ]
        else:
            expand = [
                {
                    "label": "Tags",
                    "value": tags_value,
                },
            ]

        rows.append(
            {
                "id": f"{item.get('type', '').lower()}-{item.get('id')}",
                "is_group": is_group,
                "cells": [
                    "Group" if item.get("type") == "ServiceGroup" else item.get("type", ""),
                    item.get("name", ""),
                    item.get("description", ""),
                    item.get("protocol") or "",
                    item.get("port_start") or "",
                    item.get("port_end") or "",
                    tags_value,
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


# Handles creation of a new service from modal form submission.
@login_required(login_url="login")
def post_service_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    protocol = request.POST.get("protocol", "")
    port_start = int(request.POST.get("port_start")) if request.POST.get("port_start") else None
    port_end = int(request.POST.get("port_end")) if request.POST.get("port_end") else None
    group_ids = [int(group_id) for group_id in request.POST.getlist("group_ids") if group_id]

    try:
        created_service = create_service(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
            protocol=protocol,
            port_start=port_start,
            port_end=port_end,
        )

        for group_id in group_ids:
            add_service_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=group_id,
                service_id=created_service.id,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "services",
                "modal_content_partial": "partials/modals/_service_form.html",
                "modal_supports_types": True,
                "modal_type": "item",
                "item_type_editable": False,
                "modal_type_labels": {
                    "item": "Service",
                    "group": "Group",
                },
                "error_message": f"Could not create service: {e}",
                "group_options": get_group_options_view(request, "services"),
            },
            status=400,
        )

    row = {
        "id": f"service-{created_service.id}",
        "cells": [
            "Service",
            created_service.name,
            created_service.description,
            created_service.protocol,
            created_service.port_start or "",
            created_service.port_end or "",
            [],
        ],
        "raw": created_service,
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Handles updating an existing service from modal form submission.
@login_required(login_url="login")
def update_service_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    protocol = request.POST.get("protocol", "")
    port_start = request.POST.get("port_start") or None
    port_end = request.POST.get("port_end") or None
    group_ids = [int(group_id) for group_id in request.POST.getlist("group_ids") if group_id]

    port_start = int(port_start) if port_start is not None else None
    port_end = int(port_end) if port_end is not None else None

    object_data = {
        "name": name,
        "description": description,
        "protocol": protocol,
        "port_start": port_start,
        "port_end": port_end,
        "service_groups": [{"id": group_id} for group_id in group_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service",
                "modal_mode": "update",
                "modal_row_id": f"service-{object_id}",
                "modal_object_type": "services",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_form.html",
                "modal_post_url": reverse("update-service-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "group_options": get_group_options_view(request, "services"),
                "selected_group_ids": group_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        updated_service = update_service(
            actor=request.user,
            tenant_id=tenant_id,
            service_id=object_id,
            name=name,
            description=description,
            protocol=protocol,
            port_start=port_start,
            port_end=port_end,
        )

        ServiceGroupMember.objects.filter(service_id=updated_service.id).delete()

        for group_id in group_ids:
            add_service_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=group_id,
                service_id=updated_service.id,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service",
                "modal_mode": "update",
                "modal_row_id": f"service-{object_id}",
                "modal_object_type": "services",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_form.html",
                "modal_post_url": reverse("update-service-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "group_options": get_group_options_view(request, "services"),
                "selected_group_ids": group_ids,
                "error_message": f"Could not update service: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of a service from the backend.
@login_required(login_url="login")
def delete_service_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_service(
            actor=request.user,
            tenant_id=tenant_id,
            service_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete service: {e}", status=400)

    return HttpResponse(status=204)


# Handles creation of a new service group from modal form submission.
@login_required(login_url="login")
def post_service_group_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    service_ids = [int(service_id) for service_id in request.POST.getlist("service_ids") if service_id]

    try:
        created_service_group = create_service_group(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )

        if service_ids:
            add_services_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=created_service_group.id,
                service_ids=service_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "services",
                "modal_content_partial": "partials/modals/_service_group_form.html",
                "modal_supports_types": True,
                "modal_type": "group",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Service",
                    "group": "Service Group",
                },
                "error_message": f"Could not create service group: {e}",
                "item_options": get_item_options_view(request, "services"),
            },
            status=400,
        )

    row = {
        "id": f"servicegroup-{created_service_group.id}",
        "cells": [
            "ServiceGroup",
            created_service_group.name,
            created_service_group.description,
            "-",
            "-",
            "-",
            [],
        ],
        "raw": created_service_group,
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Handles updating an existing service group from modal form submission.
@login_required(login_url="login")
def update_service_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    service_ids = [int(service_id) for service_id in request.POST.getlist("service_ids") if service_id]

    object_data = {
        "name": name,
        "description": description,
        "services": [{"id": service_id} for service_id in service_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service Group",
                "modal_mode": "update",
                "modal_row_id": f"servicegroup-{object_id}",
                "modal_object_type": "services",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_group_form.html",
                "modal_post_url": reverse("update-service-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "services"),
                "selected_service_ids": service_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_service_group(
            actor=request.user,
            tenant_id=tenant_id,
            service_group_id=object_id,
            name=name,
            description=description,
        )

        ServiceGroupMember.objects.filter(group_id=object_id).delete()

        if service_ids:
            add_services_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=object_id,
                service_ids=service_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service Group",
                "modal_mode": "update",
                "modal_row_id": f"servicegroup-{object_id}",
                "modal_object_type": "services",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_group_form.html",
                "modal_post_url": reverse("update-service-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "services"),
                "selected_service_ids": service_ids,
                "error_message": f"Could not update service group: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of a service group from the backend.
@login_required(login_url="login")
def delete_service_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_service_group(
            actor=request.user,
            tenant_id=tenant_id,
            service_group_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete service group: {e}", status=400)

    return HttpResponse(status=204)


"""
====================================================================
Tags Page
====================================================================
"""


@login_required(login_url="login")
def get_tags_page(request):
    request.session["active_page"] = "tags"
    return render(
        request,
        "tags.html",
        {
            "active_page": "tags",
            "page_title": "Tags",
            "object_type": "tags",
            "add_button_label": "Add Tag",
            "tags": get_tags_view(request),
            **get_tenant_context(request),
        },
    )


# Fetch services from the API and map them to data.
def get_tags_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        tags = get_all_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Name", "Description"]

    rows = []

    for item in tags:
        istrue = True
        results, objects = get_all_objects_with_certain_tag(
            actor=request.user, tenant_id=int(tenant_id), tag_id=item.id
        )
        logger.info("Tag %s (%s)", item.id, item.name)
        for obj_type, obj_list in objects.items():
            logger.info("View objects[%s] count = %s", obj_type, len(obj_list))
            if obj_type == "interface":
                logger.info("Interface names = %s", [getattr(obj, "name", None) for obj in obj_list])
        expand = [
            {"label": "Addresses", "value": [obj.name for obj in objects["address"]], "special_style": True},
            {"label": "Address Group", "value": [obj.name for obj in objects["addressgroup"]], "special_style": True},
            {"label": "Services", "value": [obj.name for obj in objects["service"]], "special_style": True},
            {"label": "Service Group", "value": [obj.name for obj in objects["servicegroup"]], "special_style": True},
            {"label": "Rule", "value": [obj.name for obj in objects["rule"]], "special_style": True},
            {"label": "Filter", "value": [obj.name for obj in objects["filter"]], "special_style": True},
            {"label": "Device", "value": [obj.name for obj in objects["device"]], "special_style": True},
            {"label": "Interface", "value": [obj.name for obj in objects["interface"]], "special_style": True},
        ]

        rows.append(
            {
                "id": f"tag-{item.id}",
                "istrue": istrue,
                "cells": [
                    item.name,
                    item.description,
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


"""
====================================================================
Modal Partial: Add Modal
====================================================================
"""


# Return modal configuration for each object type.
def get_add_modal_config(object_type):
    configs = {
        "devices": {
            "title": "Add Device",
            "supports_types": True,
            "default_type": "item",
            "item_type_editable": True,
            "type_labels": {
                "item": "Device",
                "group": "Device Group",
            },
            "types": {
                "item": "partials/modals/_device_form.html",
                "group": "partials/modals/_device_group_form.html",
            },
        },
        "filters": {
            "title": "Add Filter",
            "supports_types": False,
            "form_partial": "partials/modals/_filter_form.html",
        },
        "addresses": {
            "title": "Add Address",
            "supports_types": True,
            "default_type": "item",
            "item_type_editable": True,
            "type_labels": {
                "item": "Address",
                "group": "Address Group",
            },
            "types": {
                "item": "partials/modals/_address_form.html",
                "group": "partials/modals/_address_group_form.html",
            },
            "post_urls": {
                "item": reverse("post-address-view"),
                "group": reverse("post-address-group-view"),
            },
            "target": "#addresses-table",
            "swap": "beforeend",
            "submit_handler": "prepareAddressForm",
            "refresh_url": reverse("objects-addresses"),
        },
        "services": {
            "title": "Add Service",
            "supports_types": True,
            "default_type": "item",
            "item_type_editable": True,
            "type_labels": {
                "item": "Service",
                "group": "Service Group",
            },
            "types": {
                "item": "partials/modals/_service_form.html",
                "group": "partials/modals/_service_group_form.html",
            },
            "post_urls": {
                "item": reverse("post-service-view"),
                "group": reverse("post-service-group-view"),
            },
            "target": "#services-table",
            "swap": "beforeend",
            "refresh_url": reverse("objects-services"),
        },
        "tags": {
            "title": "Add Tag",
            "supports_types": False,
            "form_partial": "partials/modals/_tag_form.html",
        },
    }
    return configs[object_type]  # Return the modal config for the selected object type


# Render the Add modal with the default form for the selected object type.
@login_required(login_url="login")
def get_add_modal(request, object_type):
    config = get_add_modal_config(object_type)

    # Check if modal supports multiple types
    if config.get("supports_types"):
        selected_type = config["default_type"]
        modal_content_partial = config["types"][selected_type]
    else:
        selected_type = None
        modal_content_partial = config["form_partial"]

    modal_post_url = config.get("post_url")
    if config.get("supports_types") and config.get("post_urls"):
        modal_post_url = config["post_urls"].get(selected_type)

    context = {
        "modal_title": config["title"],
        "modal_mode": "add",
        "modal_object_type": object_type,
        "modal_type": selected_type,
        "modal_supports_types": config.get("supports_types", False),
        "item_type_editable": config.get("item_type_editable", False),
        "modal_type_labels": config.get("type_labels", {}),
        "modal_content_partial": modal_content_partial,
        "modal_post_url": modal_post_url,
        "modal_target": config.get("target"),
        "modal_swap": config.get("swap"),
        "modal_submit_handler": config.get("submit_handler"),
        "modal_refresh_url": config.get("refresh_url"),
        "object_data": {},
        "selected_group_ids": [],
        "selected_address_ids": [],
        "selected_service_ids": [],
    }

    # If object_type is address, service or device, then show all groups
    if object_type in ["addresses", "services"]:
        context["group_options"] = get_group_options_view(request, object_type)
        context["item_options"] = get_item_options_view(request, object_type)

    return render(request, "partials/_modal.html", context)


# Render the modal content when switching between item/group form types.
@login_required(login_url="login")
def get_add_modal_form_content(request, object_type, type):
    config = get_add_modal_config(object_type)

    modal_post_url = config.get("post_url")
    if config.get("supports_types") and config.get("post_urls"):
        modal_post_url = config["post_urls"].get(type)

    modal_submit_handler = config.get("submit_handler")
    if object_type == "addresses" and type == "group":
        modal_submit_handler = None

    context = {
        "modal_object_type": object_type,
        "modal_type": type,
        "modal_supports_types": config.get("supports_types", False),
        "item_type_editable": config.get("item_type_editable", False),
        "modal_type_labels": config.get("type_labels", {}),
        "modal_content_partial": config["types"][type],
        "modal_post_url": modal_post_url,
        "modal_target": config.get("target"),
        "modal_swap": config.get("swap"),
        "modal_submit_handler": modal_submit_handler,
        "modal_refresh_url": config.get("refresh_url"),
        "object_data": {
            "name": request.GET.get("name", ""),
            "description": request.GET.get("description", ""),
        },
        "selected_group_ids": [],
        "selected_address_ids": [],
        "selected_service_ids": [],
    }

    # If object_type is address, service or device, then show all groups
    if object_type in ["addresses", "services"]:
        context["group_options"] = get_group_options_view(request, object_type)
        context["item_options"] = get_item_options_view(request, object_type)

    return render(request, "partials/modals/_modal_form.html", context)


"""
====================================================================
Modal Partial: Update Modal
====================================================================
"""


# Return modal configuration for each object type.
def get_update_modal_config(object_type):
    configs = {
        "devices": {
            "title": "Update Device",
            "modal_object_type": "devices",
        },
        "devicegroup": {
            "title": "Update Device Group",
            "modal_object_type": "devices",
        },
        "filters": {
            "title": "Update Filter",
            "modal_object_type": "filters",
        },
        "address": {
            "title": "Update Address",
            "modal_object_type": "addresses",
            "modal_type": "item",
            "content_partial": "partials/modals/_address_form.html",
            "post_url_name": "update-address-view",
            "delete_url_name": "delete-address-view",
            "refresh_url_name": "objects-addresses",
            "submit_handler": "prepareAddressForm",
        },
        "addressgroup": {
            "title": "Update Address Group",
            "modal_object_type": "addresses",
            "modal_type": "group",
            "content_partial": "partials/modals/_address_group_form.html",
            "post_url_name": "update-address-group-view",
            "delete_url_name": "delete-address-group-view",
            "refresh_url_name": "objects-addresses",
            "submit_handler": None,
        },
        "service": {
            "title": "Update Service",
            "modal_object_type": "services",
            "modal_type": "item",
            "content_partial": "partials/modals/_service_form.html",
            "post_url_name": "update-service-view",
            "delete_url_name": "delete-service-view",
            "refresh_url_name": "objects-services",
            "submit_handler": None,
        },
        "servicegroup": {
            "title": "Update Service Group",
            "modal_object_type": "services",
            "modal_type": "group",
            "content_partial": "partials/modals/_service_group_form.html",
            "post_url_name": "update-service-group-view",
            "delete_url_name": "delete-service-group-view",
            "refresh_url_name": "objects-services",
            "submit_handler": None,
        },
        "tags": {
            "title": "Update Tag",
            "modal_object_type": "tags",
        },
    }
    return configs.get(object_type)


@login_required(login_url="login")
def get_update_modal(request, row_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    # Validate row_id format and extract object_type and object_id
    try:
        object_type, object_id = row_id.split("-", 1)
        object_id = int(object_id)
        tenant_id = int(tenant_id)
    except (ValueError, TypeError):
        return HttpResponse("Invalid row id.", status=400)

    # Get the modal configuration for the object type
    config = get_update_modal_config(object_type)

    # Prepare placeholders for object data and options context
    object_data = None
    options_context = {}
    selected_ids = []

    if object_type in ["address", "addressgroup"]:
        objects, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=tenant_id,
            include_global_tenant=False,
        )

        # Fetch the specific object data based on type and id
        if object_type == "address":
            object_data = next(
                (item for item in objects if item.get("type") == "Address" and item.get("id") == object_id),
                None,
            )
            object_data["ipv4_input"] = build_ip_input(
                object_data.get("ipv4_type"),
                object_data.get("ipv4Network"),
                object_data.get("ipv4Address_start"),
                object_data.get("ipv4Address_end"),
            )
            object_data["ipv6_input"] = build_ip_input(
                object_data.get("ipv6_type"),
                object_data.get("ipv6Network"),
                object_data.get("ipv6Address_start"),
                object_data.get("ipv6Address_end"),
            )
            # If the object data is found, fetch group options and selected group ids
            if object_data:
                options_context["group_options"] = get_group_options_view(request, "addresses")
                selected_ids = [int(item["id"]) for item in object_data.get("address_groups", [])]
                options_context["selected_group_ids"] = selected_ids

        elif object_type == "addressgroup":
            object_data = next(
                (item for item in objects if item.get("type") == "AddressGroup" and item.get("id") == object_id),
                None,
            )
            if object_data:
                options_context["item_options"] = get_item_options_view(request, "addresses")
                selected_ids = [int(item["id"]) for item in object_data.get("addresses", [])]
                options_context["selected_address_ids"] = selected_ids

    elif object_type in ["service", "servicegroup"]:
        objects, _, _ = get_all_services_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=tenant_id,
            include_global_tenant=False,
        )

        if object_type == "service":
            object_data = next(
                (item for item in objects if item.get("type") == "Service" and item.get("id") == object_id),
                None,
            )
            if object_data:
                options_context["group_options"] = get_group_options_view(request, "services")
                selected_ids = [int(item["id"]) for item in object_data.get("service_groups", [])]
                options_context["selected_group_ids"] = selected_ids

        elif object_type == "servicegroup":
            object_data = next(
                (item for item in objects if item.get("type") == "ServiceGroup" and item.get("id") == object_id),
                None,
            )
            if object_data:
                options_context["item_options"] = get_item_options_view(request, "services")
                selected_ids = [int(item["id"]) for item in object_data.get("services", [])]
                options_context["selected_service_ids"] = selected_ids

    if not object_data:
        return HttpResponse("Object not found.", status=404)

    context = {
        "modal_title": config["title"],
        "modal_mode": "update",
        "modal_row_id": row_id,
        "modal_object_type": config["modal_object_type"],
        "modal_type": config["modal_type"],
        "modal_supports_types": False,
        "item_type_editable": False,
        "modal_type_labels": {},
        "modal_content_partial": config["content_partial"],
        "modal_post_url": reverse(config["post_url_name"], args=[object_id]),
        "modal_delete_url": reverse(config["delete_url_name"], args=[object_id])
        if config.get("delete_url_name")
        else None,
        "modal_target": "#modal-container",
        "modal_swap": "innerHTML",
        "modal_submit_handler": config["submit_handler"],
        "modal_refresh_url": reverse(config["refresh_url_name"]),
        "object_data": object_data,
        **options_context,
    }

    return render(request, "partials/_modal.html", context)


"""
====================================================================
Modal Partial: Item/Group Options
====================================================================
"""


# Fetch all groups of given object_type, by calling all items with "type"=AddressGroup/ServiceGroup
def get_group_options_view(request, object_type):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return []

    try:
        tenant_id = int(tenant_id)

        if object_type == "addresses":
            objects, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") == "AddressGroup"
            ]

        if object_type == "services":
            objects, _, _ = get_all_services_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") == "ServiceGroup"
            ]

    except Exception:
        return []

    return []


# Fetch all item options of given object_type, excluding groups.
def get_item_options_view(request, object_type):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return []

    try:
        tenant_id = int(tenant_id)

        if object_type == "addresses":
            objects, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") != "AddressGroup"
            ]

        if object_type == "services":
            objects, _, _ = get_all_services_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") != "ServiceGroup"
            ]

    except Exception:
        return []

    return []
