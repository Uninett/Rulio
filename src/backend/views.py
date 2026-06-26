from django.shortcuts import render
from .api import (
    # Tenant
    list_tenants,
    # Object Page: Address
    get_addresses_and_groups_with_tags_endpoint,
    create_address_endpoint,
    create_address_group_endpoint,
    # Object Page: Service
    get_services_and_groups_with_tags_endpoint,
    create_service_endpoint,
    create_service_group_endpoint,
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
        "selected_tenant": request.session.get("current_tenant_id"),
    }


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
Objects Page: Address
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
    status, api_addresses = get_addresses_and_groups_with_tags_endpoint(request)

    if status != 200:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "IPv4", "IPv6", "Tags"]

    rows = []

    for item in api_addresses:
        item_type = item.get("type", "")
        is_group = item_type == "AddressGroup"

        tags_value = [tag.get("name", "") for tag in item.get("tags", [])]
        tags_display = ", ".join(tags_value) or ""
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
                    "Group" if item.get("type") == "AddressGroup" else item.get("type", ""),
                    item.get("name", ""),
                    item.get("description", ""),
                    item.get("ipv4Network") or "",
                    item.get("ipv6Network") or "",
                    tags_display,
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


# Handles creation of a new address from modal form submission.
def post_address_view(request):
    payload = Payload()  # Build a payload object from submitted form data.
    payload.name = request.POST.get("name", "")
    payload.description = request.POST.get("description", "")
    payload.tenant_id = (
        int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    )
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

    # If creation failed, re-render the modal form content with an error message.
    if status not in [200, 201]:
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
                "error_message": "Could not create address.",
            },
            status=400,
        )

    # Map the created address response into the generic table row format used by the shared table component.
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


# Handles creation of a new address group from modal form submission.
def post_address_group_view(request):
    payload = Payload()
    payload.name = request.POST.get("name", "")
    payload.description = request.POST.get("description", "")
    payload.tenant_id = (
        int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    )

    status, created_address_group = create_address_group_endpoint(request, payload)

    if status not in [200, 201]:
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
                "error_message": "Could not create address group.",
            },
            status=400,
        )

    row = {
        "id": f"{created_address_group.get('type', '').lower()}-{created_address_group.get('id')}",
        "cells": [
            created_address_group.get("type", ""),
            created_address_group.get("name", ""),
            created_address_group.get("description", ""),
            "-",
            "-",
            created_address_group.get("tags", ""),
        ],
        "expand": [
            "",
            "",
            "",
            "",
            "",
            "",
            [],
            created_address_group.get("addresses", []),
        ],
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


"""
====================================================================
Objects Page: Service
====================================================================
"""


# Render the Services tab content for the Objects page.
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


# Fetch services from the API and map them to data.
def get_services_view(request):
    status, api_services = get_services_and_groups_with_tags_endpoint(request)

    if status != 200:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "Protocol", "Port Start", "Port End", "Tags"]

    rows = []

    for item in api_services:
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
                    ", ".join(tags_value) or "",
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


# Handles creation of a new service from modal form submission.
def post_service_view(request):
    payload = Payload()
    payload.name = request.POST.get("name", "")
    payload.description = request.POST.get("description", "")
    payload.tenant_id = (
        int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    )
    payload.protocol = request.POST.get("protocol", "")
    payload.port_start = request.POST.get("port_start") or None
    payload.port_end = request.POST.get("port_end") or None

    status, created_service = create_service_endpoint(request, payload)

    if status not in [200, 201]:
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
                "error_message": "Could not create service.",
            },
            status=400,
        )

    row = {
        "id": f"{created_service.get('type', '').lower()}-{created_service.get('id')}",
        "cells": [
            created_service.get("type", ""),
            created_service.get("name", ""),
            created_service.get("description", ""),
            created_service.get("protocol", ""),
            created_service.get("port_start", ""),
            created_service.get("port_end", ""),
            created_service.get("tags", ""),
        ],
        "raw": created_service,
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Handles creation of a new service group from modal form submission.
def post_service_group_view(request):
    payload = Payload()
    payload.name = request.POST.get("name", "")
    payload.description = request.POST.get("description", "")
    payload.tenant_id = (
        int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    )

    status, created_service_group = create_service_group_endpoint(request, payload)

    if status not in [200, 201]:
        return render(
            request,
            "partials/modals/_type_content.html",
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
                "error_message": "Could not create service group.",
            },
            status=400,
        )

    row = {
        "id": f"{created_service_group.get('type', '').lower()}-{created_service_group.get('id')}",
        "cells": [
            created_service_group.get("type", ""),
            created_service_group.get("name", ""),
            created_service_group.get("description", ""),
            "-",
            "-",
            "-",
            created_service_group.get("tags", ""),
        ],
        "raw": created_service_group,
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


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
            "modal_post_url": modal_post_url,
            "modal_target": config.get("target"),
            "modal_swap": config.get("swap"),
            "modal_submit_handler": config.get("submit_handler"),
            "modal_refresh_url": config.get("refresh_url"),
        },
    )


# Render the modal content when switching between item/group form types.
def get_add_modal_form_content(request, object_type, type):
    config = get_add_modal_config(object_type)

    modal_post_url = config.get("post_url")
    if config.get("supports_types") and config.get("post_urls"):
        modal_post_url = config["post_urls"].get(type)

    modal_submit_handler = config.get("submit_handler")
    if object_type == "addresses" and type == "group":
        modal_submit_handler = None

    return render(
        request,
        "partials/modals/_modal_form.html",
        {
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
        },
    )
