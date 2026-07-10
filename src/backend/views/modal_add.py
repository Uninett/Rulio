from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from backend.utils.logger import set_up_logger

from backend.objects.tenant_objects.tenant import Tenant
from django.contrib.auth.models import User

from backend.views.modal import get_group_options_view, get_item_options_view

logger = set_up_logger(__name__)

"""
====================================================================
Modal Partial: Add Modal
====================================================================
"""


# Return modal configuration for each object type.
def get_add_modal_config(object_type):
    configs = {
        "users": {
            "title": "Create User",
            "supports_types": False,
            "form_partial": "partials/management/_user_form.html",
            "post_url": reverse("post-user-view"),
            "target": "#management-content",
            "swap": "innerHTML",
            "refresh_url": reverse("management-users"),
            "modal_refresh_target": "#management-content",
        },
        "tenants": {
            "title": "Create Tenant",
            "supports_types": False,
            "form_partial": "partials/management/_tenant_form.html",
            "post_url": reverse("post-tenant-view"),
            "target": "#management-content",
            "swap": "innerHTML",
            "refresh_url": reverse("management-tenants"),
            "modal_refresh_target": "#management-content",
        },
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
            "modal_refresh_target": "#objects-content",
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
            "modal_refresh_target": "#objects-content",
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
        "modal_refresh_target": config.get("modal_refresh_target"),
        "object_data": {},
        "selected_group_ids": [],
        "selected_address_ids": [],
        "selected_service_ids": [],
    }

    # If object_type is address, service or device, then show all groups
    if object_type in ["addresses", "services"]:
        context["group_options"] = get_group_options_view(request, object_type)
        context["item_options"] = get_item_options_view(request, object_type)

    if object_type == "users":
        context["tenant_options"] = [
            {"id": tenant.id, "name": tenant.tenant_name}
            for tenant in Tenant.objects.exclude(id=1).order_by("tenant_name")
        ]

    if object_type == "tenants":
        context["user_options"] = [
            {"id": user.id, "name": user.username} for user in User.objects.all().order_by("username")
        ]
        context["selected_user_ids"] = []

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
        "modal_refresh_target": config.get("modal_refresh_target"),
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
