# Frontend
from django.shortcuts import render
from django.urls import reverse

"""
Frontend
"""


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


def get_mock_addresses():
    return [
        {
            "type": "address",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "address",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.2",
            "ipv6": "2001:db8::2",
            "description": "Secondary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "ipv4": "10.0.0.1",
            "ipv6": "2001:db8::1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
    ]


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
            "addresses": get_mock_addresses(),
        },
    )


def get_objects_addresses(request):
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Addresses",
            "addresses": get_mock_addresses(),
        },
    )


def get_objects_services(request):
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Services",
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
