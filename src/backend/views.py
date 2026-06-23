# Frontend
from django.shortcuts import render
from .api import list_addresses
from django.urls import reverse

"""
Frontend
"""


def get_objects_toolbar_context(active_tool, add_button_label="Add Address"):
    return {
        "active_tool": active_tool,
        "toggle_items": [
            {
                "key": "addresses",
                "label": "Addresses",
                "url": reverse("objects-addresses"),
            },
            {
                "key": "services",
                "label": "Services",
                "url": reverse("objects-services"),
            },
        ],
        "add_button_label": add_button_label,
    }


# This is a temporary implementation with hardcoded data for demonstration purposes.
def get_addresses_view(request):
    status, api_addresses = list_addresses(request)

    if status != 200:
        addresses = []

    else:
        addresses = [
            {
                "type": "address" if item.get("id") else "group",
                "name": item.get("name", ""),
                "ipv4": item.get("ipv4Network") or "",
                "ipv6": item.get("ipv6Network") or "",
                "description": item.get("description", ""),
                "tags": "",
            }
            for item in api_addresses
        ]
    return addresses


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


# This is a temporary implementation with hardcoded data for demonstration purposes.
def get_objects_page(request):
    return render(
        request,
        "objects.html",
        {
            "active_page": "objects",
            "page_title": "Addresses",
            "addresses": get_addresses_view(request),
            "object_type": "addresses",
            **get_objects_toolbar_context("addresses"),
        },
    )


def get_objects_addresses(request):
    addresses = get_addresses_view(request)
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Addresses",
            "object_type": "addresses",
            "addresses": addresses,
            **get_objects_toolbar_context("addresses", add_button_label="Add Address"),
        },
    )


def get_objects_services(request):
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Services",
            "object_type": "services",
            **get_objects_toolbar_context("services", add_button_label="Add Service"),
        },
    )


def get_empty_address_row_partial(request):
    return render(request, "partials/objects/_addressesRowEdit.html")


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


def get_addresses_content(request):
    return render(request, "partials/objects/_objects_addresses.html")


def get_services_content(request):
    return render(request, "partials/objects/_objects_services.html")


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
    return configs[object_type]


def get_add_modal(request, object_type):
    config = get_add_modal_config(object_type)

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


def get_add_modal_form_content(request, object_type, type):
    config = get_add_modal_config(object_type)

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
