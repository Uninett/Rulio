from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger

from django.contrib.auth.models import User
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember

from backend.views.modal import get_group_options_view, get_item_options_view
from backend.views.objects_addresses import build_ip_input

from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)

from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)

logger = set_up_logger(__name__)


"""
====================================================================
Modal Partial: Update Modal
====================================================================
"""


# Return modal configuration for each object type.
def get_update_modal_config(object_type):
    configs = {
        "user": {
            "title": "Update User",
            "modal_object_type": "users",
            "modal_type": None,
            "content_partial": "partials/management/_user_form.html",
            "post_url_name": "update-user-view",
            "delete_url_name": None,
            "refresh_url_name": "management-users",
            "modal_refresh_target": "#management-content",
            "submit_handler": None,
        },
        "tenant": {
            "title": "Update Tenant",
            "modal_object_type": "tenants",
            "modal_type": None,
            "content_partial": "partials/management/_tenant_form.html",
            "post_url_name": "update-tenant-view",
            "delete_url_name": None,
            "refresh_url_name": "management-tenants",
            "modal_refresh_target": "#management-content",
            "submit_handler": None,
        },
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
            "modal_refresh_target": "#objects-content",
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
            "modal_refresh_target": "#objects-content",
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
            "modal_refresh_target": "#objects-content",
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
            "modal_refresh_target": "#objects-content",
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
    except (ValueError, TypeError):
        return HttpResponse("Invalid row id.", status=400)

    # Get the modal configuration for the object type
    config = get_update_modal_config(object_type)

    # Prepare placeholders for object data and options context
    object_data = None
    options_context = {}
    selected_ids = []

    if object_type == "user":
        user = User.objects.filter(id=object_id).first()

        if user:
            object_data = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "is_superuser": user.is_superuser,
            }
            options_context["tenant_options"] = [
                {"id": tenant.id, "name": tenant.tenant_name}
                for tenant in Tenant.objects.exclude(id=1).order_by("tenant_name")
            ]

    elif object_type == "tenant":
        tenant = Tenant.objects.filter(id=object_id).first()

        if tenant:
            object_data = {
                "tenant_name": tenant.tenant_name,
            }

            options_context["user_options"] = [
                {"id": user.id, "name": user.username} for user in User.objects.all().order_by("username")
            ]

            selected_ids = list(TenantUserMember.objects.filter(tenant=tenant).values_list("user_id", flat=True))
            options_context["selected_user_ids"] = selected_ids

    elif object_type in ["address", "addressgroup"]:
        if tenant_id is None:
            return HttpResponse("No tenant selected.", status=400)

        tenant_id = int(tenant_id)

        objects, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=tenant_id,
            include_global_tenant=True,
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
        if tenant_id is None:
            return HttpResponse("No tenant selected.", status=400)

        tenant_id = int(tenant_id)

        objects, _, _ = get_all_services_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=tenant_id,
            include_global_tenant=True,
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
        "modal_refresh_target": config["modal_refresh_target"],
        "object_data": object_data,
        **options_context,
    }

    return render(request, "partials/_modal.html", context)
