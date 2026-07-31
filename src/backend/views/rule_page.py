from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.services.membership import add_objects_to_rule, update_objects_in_rule
from constants import GLOBAL_TENANT_ID

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.filters.rule import Rule
from backend.objects.filters.filter import Filter
from backend.services.attribute_objects.get_address_objects import get_address_group_members
from backend.services.attribute_objects.get_service_objects import get_service_group_members
from backend.services.filter_objects.create_filter_objects import create_rule
from backend.views.modal import get_group_options_view, get_item_options_view
from backend.views.session import get_tenant_context
from django.urls import reverse

from django.http import HttpResponse


from backend.services.get import (
    get_all_objects_from_rule,
    get_filters_with_rules_with_tags_from_tenant,
    get_all_rules_with_objects_from_filter,
)

"""
====================================================================
Rule Page
====================================================================
"""


@login_required(login_url="login")
def get_rule_page(request):
    filter_id = request.GET.get("filter_id", "")
    filter_name = request.GET.get("filter_name", "")

    request.session["active_page"] = "Filters"
    return render(
        request,
        "rules.html",
        {
            "active_page": "Filters",
            "page_title": "Filter -> " + filter_name,
            "object_type": "rules",
            "add_button_label": "Add Rule",
            "current_filter_id": filter_id,
            "current_filter_name": filter_name,
            "rules": get_rules_view(request),
            **get_tenant_context(request),
        },
    )


def get_rules_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {"headers": [], "rows": []}

    tenant_id = int(tenant_id)

    headers = [
        "Name",
        "Source",
        "Destination",
        "Services",
        "Action",
        "Log",
        "Count",
        "Description",
        "Created",
        "Modified",
        "Tags",
    ]

    filter_id = request.GET.get("filter_id")
    if not filter_id:
        return {"headers": headers, "rows": []}

    try:
        rules = get_all_rules_with_objects_from_filter(
            request.user,
            tenant_id,
            int(filter_id),
        )
    except Exception as e:
        print(f"Error fetching rules with objects for filter {filter_id}: {e}")
        return {"headers": headers, "rows": []}

    rows = []

    for rule in rules:
        try:
            rule_obj = Rule.objects.get(id=rule["rule_id"])
            rule_tag_names = [tag.name for tag in rule_obj.get_tags()]
        except Exception as e:
            print(f"Error fetching tags for rule {rule['rule_id']}: {e}")
            rule_tag_names = []

        source_objects = []
        destination_objects = []
        service_objects = []

        for obj in rule["objects"]:
            object_type = (obj.get("object_type") or "").lower()
            object_id = obj.get("object_id")
            object_name = obj.get("object_name") or ""
            row_id = f"{object_type}-{object_id}" if object_type and object_id else ""

            navigate_url = ""
            if object_type in ["address", "addressgroup"]:
                navigate_url = reverse("objects") + f"?object_type=addresses&expand_id={row_id}"
            elif object_type in ["service", "servicegroup"]:
                navigate_url = reverse("objects") + f"?object_type=services&expand_id={row_id}"

            item = {
                "name": object_name,
                "row_id": row_id,
                "navigate_url": navigate_url,
                "hover_text": object_name,
            }

            match object_type:
                case "address" | "addressgroup":
                    if obj["match_type"] == "source":
                        source_objects.append(item)
                    elif obj["match_type"] == "destination":
                        destination_objects.append(item)

                case "service" | "servicegroup":
                    service_objects.append(item)

        rows.append(
            {
                "id": f"rule-{rule['rule_id']}",
                "is_group": False,
                "cells": [
                    rule["rule_name"],
                    source_objects,
                    destination_objects,
                    service_objects,
                    rule["rule_action"],
                    rule["rule_log_type"],
                    str(rule["rule_hit_count"]),
                    rule["rule_description"] or "",
                    rule["rule_date_created"].strftime("%Y-%m-%d %H:%M") if rule["rule_date_created"] else "",
                    rule["rule_date_changed"].strftime("%Y-%m-%d %H:%M") if rule["rule_date_changed"] else "",
                    rule_tag_names,
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


@login_required(login_url="login")
def post_rule_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    action = request.POST.get("action", "")
    log_type = request.POST.get("log_type", "")
    filter_id = request.POST.get("filter_id", "")
    enable = request.POST.get("enable") == "on"

    filter_obj = Filter.objects.filter(id=filter_id).first()
    if not filter_obj:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": {
                    "name": name,
                    "description": description,
                    "action": action,
                    "log_type": log_type,
                    "filter_id": filter_id,
                },
                "error_message": f"Filter with ID {filter_id} does not exist.",
            },
            status=400,
        )

    object_data = {
        "name": name,
        "description": description,
        "action": action,
        "log_type": log_type,
        "filter_id": filter_id,
        "source_ids": request.POST.get("source_ids", ""),
        "destination_ids": request.POST.get("destination_ids", ""),
        "service_ids": request.POST.get("service_ids", ""),
    }

    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": object_data,
                "error_message": "Tenant not set.",
            },
            status=400,
        )

    if not all([name, action, log_type, filter_id]):
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": object_data,
                "error_message": "Missing required fields.",
            },
            status=400,
        )

    tenant_id = int(tenant_id)

    try:
        new_rule = create_rule(
            actor=request.user,
            name=name,
            description=description,
            action=action,
            log_type=log_type,
            filter=filter_obj,
            tenant_id=tenant_id,
            hit_count=0,
            enable=enable,
        )

        source_ids_raw = request.POST.get("source_ids", "")
        destination_ids_raw = request.POST.get("destination_ids", "")
        service_ids_raw = request.POST.get("service_ids", "")

        source_ordered, source_grouped = parse_typed_ids(source_ids_raw)
        destination_ordered, destination_grouped = parse_typed_ids(destination_ids_raw)
        service_ordered, service_grouped = parse_typed_ids(service_ids_raw)

        source_cache = fetch_objects_by_type(source_grouped, tenant_id)
        destination_cache = fetch_objects_by_type(destination_grouped, tenant_id)
        service_cache = fetch_objects_by_type(service_grouped, tenant_id)

        source_objects = build_ordered_object_list(source_ordered, source_cache)
        destination_objects = build_ordered_object_list(destination_ordered, destination_cache)
        service_objects = build_ordered_object_list(service_ordered, service_cache)

        if source_objects:
            add_objects_to_rule(
                actor=request.user,
                tenant_id=tenant_id,
                rule_id=new_rule.id,
                match_type="source",
                objects=source_objects,
            )

        if destination_objects:
            add_objects_to_rule(
                actor=request.user,
                tenant_id=tenant_id,
                rule_id=new_rule.id,
                match_type="destination",
                objects=destination_objects,
            )

        if service_objects:
            add_objects_to_rule(
                actor=request.user,
                tenant_id=tenant_id,
                rule_id=new_rule.id,
                match_type="service",
                objects=service_objects,
            )

    except Exception as e:
        print(f"Error creating rule: {e}")
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": object_data,
                "error_message": f"Error creating rule: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


@login_required(login_url="login")
def update_rule_view(request, rule_id):
    rule = Rule.objects.filter(id=rule_id).first()
    if not rule:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "error_message": f"Rule with ID {rule_id} does not exist.",
            },
            status=400,
        )

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    action = request.POST.get("action", "")
    log_type = request.POST.get("log_type", "")
    enable = request.POST.get("enable") == "on"



    if not all([name, action, log_type]):
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": {
                    "name": name,
                    "description": description,
                    "action": action,
                    "log_type": log_type,
                    "filter_id": rule.filter.id if rule.filter else "",
                },
                "error_message": "Missing required fields.",
            },
            status=400,
        )

    try:
        rule.name = name
        rule.description = description
        rule.action = action
        rule.log_type = log_type
        rule.enable = enable
        rule.save()

        source_ids_raw = request.POST.get("source_ids", "")
        destination_ids_raw = request.POST.get("destination_ids", "")
        service_ids_raw = request.POST.get("service_ids", "")

        source_ordered, source_grouped = parse_typed_ids(source_ids_raw)
        destination_ordered, destination_grouped = parse_typed_ids(destination_ids_raw)
        service_ordered, service_grouped = parse_typed_ids(service_ids_raw)

        tenant_id = int(request.session.get("current_tenant_id"))

        source_cache = fetch_objects_by_type(source_grouped, tenant_id)
        destination_cache = fetch_objects_by_type(destination_grouped, tenant_id)
        service_cache = fetch_objects_by_type(service_grouped, tenant_id)

        source_objects = build_ordered_object_list(source_ordered, source_cache)
        destination_objects = build_ordered_object_list(destination_ordered, destination_cache)
        service_objects = build_ordered_object_list(service_ordered, service_cache)

        update_objects_in_rule(
            actor=request.user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="source",
            objects=source_objects,
        )

        update_objects_in_rule(
            actor=request.user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="destination",
            objects=destination_objects,
        )

        update_objects_in_rule(
            actor=request.user,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type="service",
            objects=service_objects,
        )

    except Exception as e:
        print(f"Error updating rule: {e}")
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": {
                    "name": name,
                    "description": description,
                    "action": action,
                    "log_type": log_type,
                    "filter_id": rule.filter.id if rule.filter else "",
                },
                "error_message": f"Error updating rule: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


@login_required(login_url="login")
def get_rule_selector_modal(request, selector_type):
    selected_ids_raw = request.GET.get("selected_ids", "")
    selected_object_ids = [value for value in selected_ids_raw.split(",") if value]

    context = {
        "modal_title": f"Edit {selector_type.title()}",
        "modal_mode": "submodal",
        "modal_object_type": "rule-selector",
        "modal_content_partial": "partials/modals/_rule_selector_modal.html",
        "selector_type": selector_type,
        "modal_instance_id": f"submodal-{selector_type}",
        "modal_is_submodal": True,
        "selected_object_ids": selected_object_ids,
    }

    if selector_type in ["source", "destination"]:
        item_options = get_item_options_view(request, "addresses")
        group_options = get_group_options_view(request, "addresses")

        for item in item_options:
            item["selector_id"] = f"address-{item['id']}"

        for group in group_options:
            group["selector_id"] = f"addressgroup-{group['id']}"

        context["item_options"] = item_options
        context["group_options"] = group_options

    elif selector_type == "service":
        item_options = get_item_options_view(request, "services")
        group_options = get_group_options_view(request, "services")

        for item in item_options:
            item["selector_id"] = f"service-{item['id']}"

        for group in group_options:
            group["selector_id"] = f"servicegroup-{group['id']}"

        context["item_options"] = item_options
        context["group_options"] = group_options

    return render(request, "partials/_modal.html", context)


def parse_typed_ids(raw_value: str) -> tuple[list[tuple[str, int]], dict[str, set[int]]]:
    ordered = []
    grouped = {}

    for token in (raw_value or "").split(","):
        token = token.strip()
        if not token or "-" not in token:
            continue

        object_type, object_id = token.split("-", 1)

        try:
            object_id = int(object_id)
        except ValueError:
            continue

        ordered.append((object_type, object_id))
        grouped.setdefault(object_type, set()).add(object_id)

    return ordered, grouped


def fetch_objects_by_type(grouped_ids: dict[str, set[int]], tenant_id: int) -> dict[str, dict[int, object]]:
    model_map = {
        "address": Address,
        "addressgroup": AddressGroup,
        "service": Service,
        "servicegroup": ServiceGroup,
    }

    result = {}

    for object_type, ids in grouped_ids.items():
        model = model_map.get(object_type)
        if not model or not ids:
            result[object_type] = {}
            continue

        queryset = model.objects.filter(id__in=ids, tenant_id__in=[tenant_id, GLOBAL_TENANT_ID])
        result[object_type] = {obj.id: obj for obj in queryset}

    return result


def build_ordered_object_list(
    ordered_ids: list[tuple[str, int]],
    object_cache: dict[str, dict[int, object]],
) -> list:
    objects = []

    for object_type, object_id in ordered_ids:
        obj = object_cache.get(object_type, {}).get(object_id)
        if obj is not None:
            objects.append(obj)

    return objects
