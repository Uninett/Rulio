from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.urls import reverse

from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember

from backend.services.attribute_objects.create_attribute_objects import (
    create_address,
    create_address_group,
    create_service,
    create_service_group,
)

from backend.services.membership import (
    add_addresses_to_group,
    add_services_to_group,
)

from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)

from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)


"""
====================================================================
Login Page
====================================================================
"""


# TODO: Only allow redirect to other pages if user is authenticated. Otherwise, redirect to login page.
# TODO: Only redirect to login page if logged out. The user should not be able to access the page without logged out.
def get_login_page(request):
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


# TODO: Add a logout view that clears the session and redirects to the login page.

"""
====================================================================
Tenant
====================================================================
"""


# Gets the list of tenants from the backend API function list_tenants()
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


"""
====================================================================
Device Page
====================================================================
"""


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


"""
====================================================================
Objects Page: Address
====================================================================
"""


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


# Handles creation of a new address from modal form submission.
def post_address_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    addr_type = request.POST.get("addr_type", "host")
    ipv4_type = request.POST.get("ipv4_type") or None
    ipv6_type = request.POST.get("ipv6_type") or None
    ipv4Network = request.POST.get("ipv4Network") or None
    ipv6Network = request.POST.get("ipv6Network") or None
    ipv4Address_start = request.POST.get("ipv4Address_start") or None
    ipv4Address_end = request.POST.get("ipv4Address_end") or None
    ipv6Address_start = request.POST.get("ipv6Address_start") or None
    ipv6Address_end = request.POST.get("ipv6Address_end") or None
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
            add_addresses_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=group_id,
                address_ids=[created_address.id],
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


# Handles creation of a new address group from modal form submission.
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
            add_services_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=group_id,
                service_ids=[created_service.id],
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


# Handles creation of a new service group from modal form submission.
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
    }

    # If object_type is address, service or device, then show all groups
    if object_type in ["addresses", "services"]:
        context["group_options"] = get_group_options_view(request, object_type)
        context["item_options"] = get_item_options_view(request, object_type)

    return render(request, "partials/_modal.html", context)


# Render the modal content when switching between item/group form types.
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
    }

    # If object_type is address, service or device, then show all groups
    if object_type in ["addresses", "services"]:
        context["group_options"] = get_group_options_view(request, object_type)
        context["item_options"] = get_item_options_view(request, object_type)

    return render(request, "partials/modals/_modal_form.html", context)


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
            api_objects = get_all_addresses_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in api_objects
                if item.get("type") == "AddressGroup"
            ]

        if object_type == "services":
            api_objects = get_all_services_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in api_objects
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
            api_objects = get_all_addresses_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in api_objects
                if item.get("type") != "AddressGroup"
            ]

        if object_type == "services":
            api_objects = get_all_services_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in api_objects
                if item.get("type") != "ServiceGroup"
            ]

    except Exception:
        return []

    return []
