# Frontend
from django.shortcuts import render

"""
Frontend
"""


def get_devices_page(request):
    return render(
        request,
        "devices.html",
        {
            "active_page": "devices",
        },
    )


def get_filters_page(request):
    return render(
        request,
        "filters.html",
        {
            "active_page": "filters",
        },
    )


# This is a temporary implementation with hardcoded data for demonstration purposes.
def get_objects_page(request):
    addresses = [
        {
            "type": "address",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "address",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
        {
            "type": "group",
            "name": "ntnu-dns-1",
            "addresses": "ntnu-dns-1",
            "description": "Primary DNS server",
            "tags": "admin",
        },
    ]

    return render(
        request,
        "objects.html",
        {
            "active_page": "objects",
            "addresses": addresses,
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
        },
    )
