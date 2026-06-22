# Frontend
from django.shortcuts import render
from .api import list_addresses
from django.urls import reverse
from .api import list_addresses

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
            "active_tool": "addresses",
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
            "add_button_label": "Add Address",
            "addresses": get_addresses_view(request),
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
            "addresses": addresses,
            **get_objects_toolbar_context("addresses"),
        },
    )


def get_objects_services(request):
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Services",
            **get_objects_toolbar_context("services"),
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
            "add_button_label": "Add Tag",
        },
    )
