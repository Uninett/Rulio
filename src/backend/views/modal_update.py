from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from backend.objects.attributes.tag import Tag
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)
from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)
from backend.services.get import (
    get_all_device_groups_and_devices_with_tags_from_tenant,
    get_all_objects_from_rule,
    get_all_tags_from_object,
    get_filter_with_rules_and_tags,
    get_rule_with_tags_from_tenant,
)
from backend.utils.logger import set_up_logger
from backend.views.modal import get_group_options_view, get_item_options_view
from backend.views.objects_addresses import build_ip_input
from backend.views.search import get_tags_search_results
from constants import GLOBAL_TENANT_ID

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
            "delete_url_name": "delete-user-view",
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
            "delete_url_name": "delete-tenant-view",
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
            "modal_type": "group",
            "content_partial": "partials/modals/_device_group_form.html",
            "post_url_name": "update-device-group-view",
            "delete_url_name": "delete-device-group-view",
            "refresh_url_name": "devices",
            "modal_refresh_target": "#devices-content",
            "submit_handler": None,
        },
        "filter": {
            "title": "Update Filter",
            "modal_object_type": "filters",
            "modal_type": "item",
            "content_partial": "partials/modals/_filter_form.html",
            "post_url_name": "update-filter-view",
            "delete_url_name": "delete-filter-view",
            "refresh_url_name": "filters-content",
            "modal_refresh_target": "#filters-content",
            "submit_handler": None,
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
        "tag": {
            "title": "Update Tag",
            "modal_object_type": "tags",
            "modal_type": None,
            "content_partial": "partials/modals/_tag_form.html",
            "post_url_name": "update-tag-view",
            "delete_url_name": "delete-tag-view",
            "refresh_url_name": "tags",
            "modal_refresh_target": "#tags-content",
            "submit_handler": None,
        },
        "rule": {
            "title": "Update Rule",
            "modal_object_type": "rules",
            "modal_type": "item",
            "content_partial": "partials/modals/_rule_form.html",
            "post_url_name": "update-rule-view",
            "delete_url_name": "delete-rule-view",
            "refresh_url_name": "rules-content",
            "modal_refresh_target": "#rules-content",
            "submit_handler": None,
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
    if not config:
        return HttpResponse("Unsupported object type.", status=400)

    # Prepare placeholders for object data and options context
    object_data = None
    options_context = {}
    selected_ids = []
    object_tags = []

    if (
        object_type in ["device", "devicegroup", "address", "addressgroup", "service", "servicegroup", "rule", "filter"]
        and tenant_id is not None
    ):
        try:
            object_tags = get_all_tags_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_id=object_id,
                object_type=object_type,
            )
        except Exception:
            object_tags = []

    if object_type == "user":
        user = User.objects.filter(id=object_id).first()

        if user:
            membership = TenantUserMember.objects.filter(user=user).exclude(tenant_id=GLOBAL_TENANT_ID).first()

            object_data = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "tenant_id": membership.tenant_id if membership else "",
                "is_tenant_admin": (membership.role == TenantUserMember.TenantRole.ADMIN if membership else False),
            }

            options_context["tenant_options"] = [
                {"id": tenant.id, "name": tenant.tenant_name}
                for tenant in Tenant.objects.exclude(id=GLOBAL_TENANT_ID).order_by("tenant_name")
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

        elif object_type in ["device", "devicegroup"]:
            if tenant_id is None:
                return HttpResponse("No tenant selected.", status=400)

            tenant_id = int(tenant_id)

            objects, _, _ = get_all_device_groups_and_devices_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
                include_global_tenant=True,
            )

            # Fetch the specific object data based on type and id
            if object_type == "device":
                object_data = next(
                    (item for item in objects if item.get("type") == "Device" and item.get("id") == object_id),
                    None,
                )
                if object_data:
                    options_context["group_options"] = get_group_options_view(request, "devices")
                    selected_ids = [int(item["id"]) for item in object_data.get("device_groups", [])]
                    options_context["selected_group_ids"] = selected_ids

            elif object_type == "devicegroups":
                object_data = next(
                    (item for item in objects if item.get("type") == "DeviceGroups" and item.get("id") == object_id),
                    None,
                )
                if object_data:
                    options_context["item_options"] = get_item_options_view(request, "devices")
                    selected_ids = [int(item["id"]) for item in object_data.get("devices", [])]
                    options_context["selected_device_ids"] = selected_ids

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

    elif object_type == "tag":
        if tenant_id is None:
            return HttpResponse("No tenant selected.", status=400)

        try:
            tag = Tag.objects.get(id=object_id, tenant_id=tenant_id)
            object_data = {
                "name": tag.name,
                "description": tag.description,
                "color": tag.color,
            }
        except Tag.DoesNotExist:
            object_data = None

    elif object_type == "rule":
        if tenant_id is None:
            return HttpResponse("No tenant selected.", status=400)

        try:
            rule, tags = get_rule_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
                rule_id=object_id,
                include_global_tenant=True,
            )

            if rule is None:
                return HttpResponse("Object not found.", status=404)

            (
                source_address_objects,
                destination_address_objects,
                source_service_objects,
                destination_service_objects,
            ) = get_all_objects_from_rule(
                actor=request.user,
                tenant_id=tenant_id,
                rule_id=rule.id,
            )

            def get_selector_ids(objects):
                return [
                    obj.get("selector_id") or obj.get("row_id")
                    for obj in objects
                    if obj.get("selector_id") or obj.get("row_id")
                ]

            object_data = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "action": rule.action,
                "log_type": rule.log_type,
                "enable": rule.enable,
                "filter_id": rule.filter_id,
                "tags": tags,
                "source_address_ids": get_selector_ids(source_address_objects),
                "source_address_names": [obj.get("name", "") for obj in source_address_objects],
                "destination_address_ids": get_selector_ids(destination_address_objects),
                "destination_address_names": [obj.get("name", "") for obj in destination_address_objects],
                "source_service_ids": get_selector_ids(source_service_objects),
                "source_service_names": [obj.get("name", "") for obj in source_service_objects],
                "destination_service_ids": get_selector_ids(destination_service_objects),
                "destination_service_names": [obj.get("name", "") for obj in destination_service_objects],
            }

        except ObjectDoesNotExist:
            return HttpResponse("Object not found.", status=404)

        except Exception:
            logger.exception(
                "Error fetching rule data for rule id=%s",
                object_id,
            )
            return HttpResponse("Error fetching rule data.", status=500)

    elif object_type == "filter":
        if tenant_id is None:
            return HttpResponse("No tenant selected.", status=400)

        try:
            filter_data = get_filter_with_rules_and_tags(
                actor=request.user,
                tenant_id=tenant_id,
                filter_id=object_id,
            )

            object_data = {
                "id": filter_data["filter_id"],
                "name": filter_data["filter_name"],
                "description": filter_data["filter_description"],
                "enable": filter_data["filter_enable"],
                "rules": filter_data["rules"],
                "tags": filter_data["tags"],
            }

        except ObjectDoesNotExist:
            return HttpResponse("Object not found.", status=404)

        except Exception:
            logger.exception(
                "Error fetching filter data for filter id=%s",
                object_id,
            )
            return HttpResponse("Error fetching filter data.", status=500)

    if not object_data:
        return HttpResponse("Object not found.", status=404)
    modal_refresh_url = reverse(config["refresh_url_name"])

    if object_type == "rule":
        filter_id = object_data.get("filter_id")

        if filter_id:
            modal_refresh_url += f"?filter_id={filter_id}"

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
        "modal_refresh_url": modal_refresh_url,
        "modal_refresh_target": config["modal_refresh_target"],
        "object_data": object_data,
        "search_results": get_tags_search_results(request, ""),
        "object_tags": object_tags,
        **options_context,
    }

    return render(request, "partials/_modal.html", context)
