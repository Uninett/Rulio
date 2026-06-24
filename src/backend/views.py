from django.shortcuts import render
from django.http import HttpResponse
from .api import (
    get_addresses_and_groups_with_tags_endpoint,
    list_tenants,
    get_services_and_groups_with_tags_endpoint,
    create_address_endpoint,
)
from django.urls import reverse


class Payload:
    pass


"""
====================================================================
Tenant
====================================================================
"""


# Gets the list of tenants from the backend API function list_tenants()
def get_tenants_view(request):
    status, api_tenants = list_tenants(request)

    if status != 200:
        return []  # If call failed, return an empty list

    return [
        {
            "id": item.get("id"),
            "name": item.get("tenant_name"),
        }
        for item in api_tenants
    ]


# Builds the data that the templates need in order to render the tenant dropdown correctly
def get_tenant_context(request):
    return {
        "tenants": get_tenants_view(request),
        "selected_tenant": request.session.get("tenant_id"),
    }


# Reads the currently selected tenant from the session (temporary solution until set_tenant api endpoint is refactored)
def set_selected_tenant(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant")

        if tenant_id:
            request.session["tenant_id"] = tenant_id
        else:
            request.session.pop("tenant_id", None)

        return HttpResponse(status=204)

    return HttpResponse(status=405)


"""
====================================================================
Device Page
====================================================================
"""


#
def get_devices_page(request):
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


def get_filters_page(request):
    return render(
        request,
        "filters.html",
        {
            "active_page": "filters",
            "page_title": "Filters",
            "object_type": "filters",
            "add_button_label": "Add Filter",
            **get_tenant_context(request),
        },
    )


"""
====================================================================
Objects Page
====================================================================
"""


def get_objects_page(request):
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


# Render the Addresses tab content for the Objects page.
def get_objects_addresses(request):
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Addresses",
            "object_type": "addresses",
            "addresses": get_addresses_view(request),  # Address data for the page
            **get_objects_toolbar_context(
                "addresses", add_button_label="Add Address"
            ),  # Render the Objects page with Addresses as the active tab.
        },
    )


# Fetch addresses from the API and map them to data.
def get_addresses_view(request):
    status, api_objects = get_addresses_and_groups_with_tags_endpoint(request)

    if status != 200:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "IPv4", "IPv6", "Tags"]

    rows = [
        {
            "id": f"{item.get('type', '').lower()}-{item.get('id')}",
            "cells": [
                item.get("type", ""),
                item.get("name", ""),
                item.get("description", ""),
                item.get("ipv4Network") or "-",
                item.get("ipv6Network") or "-",
                item.get("tags", ""),
            ],
            "expand": [
                item.get("ipv4_type", ""),
                item.get("ipv6_type", ""),
                item.get("ipv4Address_start") or "",
                item.get("ipv4Address_end") or "",
                item.get("ipv6Address_start") or "",
                item.get("ipv6Address_end") or "",
                item.get("address_groups", []),
                item.get("addresses", []),
            ],
        }
        for item in api_objects
    ]

    return {
        "headers": headers,
        "rows": rows,
    }


# Fetch services from the API and map them to data.
def get_services_view(request):
    status, api_services = get_services_and_groups_with_tags_endpoint(request)

    if status != 200:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "Protocol", "Port Start", "Port End", "Tags"]

    rows = [
        {
            "id": item.get("id", ""),
            "cells": [
                item.get("type", ""),
                item.get("name", ""),
                item.get("description", ""),
                item.get("protocol", ""),
                item.get("port_start", ""),
                item.get("port_end", ""),
                item.get("tags", ""),
            ],
            "raw": item,
        }
        for item in api_services
    ]

    return {
        "headers": headers,
        "rows": rows,
    }


# Render an empty editable address row.
def get_empty_address_row_partial(request):
    return render(request, "partials/objects/_addressesRowEdit.html")


# Build and render a saved address row from submitted form data.
def post_address_row_partial(request):
    address = {
        "name": request.POST.get("name", ""),
        "description": request.POST.get("description", ""),
        "type": request.POST.get("type", ""),
        "group": request.POST.get("group", ""),
        "referenced_to": request.POST.get("referenced_to", ""),
        "addresses": request.POST.get("addresses", ""),
        "tags": request.POST.get("tags", ""),
    }
    return render(request, "partials/objects/_tableRow.html", {"address": address})


def post_address_view(request):
    payload = Payload()
    payload.name = request.POST.get("name", "")
    payload.description = request.POST.get("description", "")
    payload.tenant_id = int(request.session.get("tenant_id")) if request.session.get("tenant_id") else None
    payload.addr_type = request.POST.get("addr_type", "host")
    payload.ipv4_type = request.POST.get("ipv4_type") or None
    payload.ipv6_type = request.POST.get("ipv6_type") or None
    payload.ipv4Network = request.POST.get("ipv4Network") or None
    payload.ipv6Network = request.POST.get("ipv6Network") or None
    payload.ipv4Address_start = request.POST.get("ipv4Address_start") or None
    payload.ipv4Address_end = request.POST.get("ipv4Address_end") or None
    payload.ipv6Address_start = request.POST.get("ipv6Address_start") or None
    payload.ipv6Address_end = request.POST.get("ipv6Address_end") or None

    status, created_address = create_address_endpoint(request, payload)

    if status not in [200, 201]:
        return render(
            request,
            "partials/modals/_type_content.html",
            {
                "modal_object_type": "addresses",
                "modal_content_partial": "partials/modals/_addresses_form.html",
                "modal_supports_types": True,
                "modal_type": "item",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Address",
                    "group": "Group",
                },
                "error_message": "Could not create address.",
            },
            status=400,
        )

    row = {
        "id": f"{created_address.get('type', '').lower()}-{created_address.get('id')}",
        "cells": [
            created_address.get("addr_type", ""),
            created_address.get("name", ""),
            created_address.get("description", ""),
            created_address.get("ipv4Network") or "-",
            created_address.get("ipv6Network") or "-",
            created_address.get("tags", ""),
        ],
        "expand": [
            created_address.get("ipv4_type", ""),
            created_address.get("ipv6_type", ""),
            created_address.get("ipv4Address_start") or "",
            created_address.get("ipv4Address_end") or "",
            created_address.get("ipv6Address_start") or "",
            created_address.get("ipv6Address_end") or "",
            created_address.get("address_groups", []),
            created_address.get("addresses", []),
        ],
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Render the Services tab content for the Objects page. TODO: Create get_services_view.
def get_objects_services(request):
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


"""
====================================================================
Tags Page
====================================================================
"""


def get_tags_page(request):
    return render(
        request,
        "tags.html",
        {
            "active_page": "tags",
            "page_title": "Tags",
            "object_type": "tags",
            "add_button_label": "Add Tag",
            **get_tenant_context(request),
        },
    )


"""
====================================================================
Modal Partial
====================================================================
"""


# Return modal configuration for each object type.
def get_add_modal_config(object_type):
    configs = {
        "devices": {
            "title": "Add Device",
            "supports_types": True,
            "default_type": "item",
            "item_type_editable": True,  # Device object contains a type (i.e. host, switch etc.)
            "type_labels": {
                "item": "Device",
                "group": "Device Group",
            },
            "types": {
                "item": "partials/modals/_devices_form.html",
                "group": "partials/modals/_device_groups_form.html",
            },
        },
        "filters": {
            "title": "Add Filter",
            "supports_types": False,
            "form_partial": "partials/modals/_filters_form.html",
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
                "item": "partials/modals/_addresses_form.html",
                "group": "partials/modals/_address_groups_form.html",
            },
            "post_url": reverse("post-address-view"),
            "target": "#addresses-table",
            "swap": "beforeend",
            "submit_handler": "prepareAddressForm",
        },
        "services": {
            "title": "Add Service",
            "supports_types": True,
            "default_type": "item",  # Address object contains a type (i.e. host, switch etc.)
            "item_type_editable": False,
            "type_labels": {
                "item": "Service",
                "group": "Service Group",
            },
            "types": {
                "item": "partials/modals/_services_form.html",
                "group": "partials/modals/_service_groups_form.html",
            },
        },
        "tags": {
            "title": "Add Tag",
            "supports_types": False,
            "form_partial": "partials/modals/_tags_form.html",
        },
    }
    return configs[object_type]  # Return the modal config for the selected object type


# Render the Add modal with the default form for the selected object type.
def get_add_modal(request, object_type):
    config = get_add_modal_config(object_type)

    # Check if modal supports multiple types
    if config.get("supports_types"):
        selected_type = config["default_type"]
        modal_content_partial = config["types"][selected_type]
    else:
        selected_type = None
        modal_content_partial = config["form_partial"]

    return render(
        request,
        "partials/_modal.html",
        {
            "modal_title": config["title"],
            "modal_mode": "add",
            "modal_object_type": object_type,
            "modal_type": selected_type,
            "modal_supports_types": config.get("supports_types", False),
            "item_type_editable": config.get("item_type_editable", False),
            "modal_type_labels": config.get("type_labels", {}),
            "modal_content_partial": modal_content_partial,
            "modal_post_url": config.get("post_url"),
            "modal_target": config.get("target"),
            "modal_swap": config.get("swap"),
            "modal_submit_handler": config.get("submit_handler"),
        },
    )


# Render the modal content when switching between item/group form types.
def get_add_modal_form_content(request, object_type, type):
    config = get_add_modal_config(object_type)  # Load modal settings for this object type

    return render(
        request,
        "partials/modals/_type_content.html",
        {
            "modal_object_type": object_type,
            "modal_type": type,
            "modal_supports_types": config.get("supports_types", False),
            "item_type_editable": config.get("item_type_editable", False),
            "modal_type_labels": config.get("type_labels", {}),
            "modal_content_partial": config["types"][type],
        },
    )
