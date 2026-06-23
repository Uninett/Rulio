from django.shortcuts import render
from .api import get_addresses_and_groups_with_tags_endpoint
from django.urls import reverse

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
        return []

    addresses = [
        {
            "id": f"{item.get('type', '').lower()}-{item.get('id')}",
            "type": item.get("type", ""),
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "ipv4": item.get("ipv4Network") or "-",
            "ipv6": item.get("ipv6Network") or "-",
            "tags": item.get("tags", ""),
            "ipv4_type": item.get("ipv4_type", ""),
            "ipv6_type": item.get("ipv6_type", ""),
            "ipv4_start": item.get("ipv4Address_start") or "",
            "ipv4_end": item.get("ipv4Address_end") or "",
            "ipv6_start": item.get("ipv6Address_start") or "",
            "ipv6_end": item.get("ipv6Address_end") or "",
            "address_groups": item.get("address_groups", []),
            "group_addresses": item.get("addresses", []),
        }
        for item in api_objects
    ]

    return addresses


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
    return render(request, "partials/objects/_addressesRow.html", {"address": address})


# Render the Services tab content for the Objects page. TODO: Create get_services_view.
def get_objects_services(request):
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Services",
            "object_type": "services",
            # "services": get_services_view(request), # Service data for the page
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
            "type_labels": {
                "item": "Address",
                "group": "Address Group",
            },
            "types": {
                "item": "partials/modals/_addresses_form.html",
                "group": "partials/modals/_address_groups_form.html",
            },
        },
        "services": {
            "title": "Add Service",
            "supports_types": True,
            "default_type": "item",
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
            "modal_type_labels": config.get("type_labels", {}),
            "modal_content_partial": modal_content_partial,
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
            "modal_type_labels": config.get("type_labels", {}),
            "modal_content_partial": config["types"][type],
        },
    )
