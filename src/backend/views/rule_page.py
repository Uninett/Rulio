from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.services.delete import delete_rule
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.membership import add_objects_to_rule, update_objects_in_rule
from constants import GLOBAL_TENANT_ID

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.filters.rule import Rule
from backend.objects.filters.filter import Filter
from backend.services.filter_objects.create_filter_objects import create_rule
from backend.views.modal import get_group_options_view, get_item_options_view
from backend.views.session import get_tenant_context
from django.urls import reverse

from django.http import HttpResponse, HttpResponseBadRequest

from backend.services.get import (
    get_all_rules_with_objects_from_filter,
)

from django.db import transaction


ADDRESS_OBJECT_TYPES = {"address", "addressgroup"}
SERVICE_OBJECT_TYPES = {"service", "servicegroup"}



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


@login_required(login_url="login")
def get_rules_content(request):
    filter_id = request.GET.get("filter_id", "")
    filter_name = request.GET.get("filter_name", "")

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": f"Filter -> {filter_name}" if filter_name else "Rules",
            "page_title": f"Filter -> {filter_name}" if filter_name else "Rules",
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

    # Description, Created, and Modified have moved to the expandable section.
    headers = [
        "Name",
        "Src-Address",
        "Dst-Address",
        "Src-Service",
        "Dst-Service",
        "Action",
        "Log",
        "Count",
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
    except Exception as exc:
        print(f"Error fetching rules with objects for filter {filter_id}: {exc}")
        return {"headers": headers, "rows": []}

    rows = []

    for rule in rules:
        try:
            rule_obj = Rule.objects.get(id=rule["rule_id"])
            rule_tag_names = [tag.name for tag in rule_obj.get_tags()]
        except Exception as exc:
            print(f"Error fetching tags for rule {rule['rule_id']}: {exc}")
            rule_tag_names = []

        source_address_objects = []
        destination_address_objects = []
        source_service_objects = []
        destination_service_objects = []

        for obj in rule["objects"]:
            object_type = (obj.get("object_type") or "").lower()
            object_id = obj.get("object_id")
            object_name = obj.get("object_name") or ""
            match_type = obj.get("match_type")

            row_id = f"{object_type}-{object_id}" if object_type and object_id else ""

            navigate_url = ""

            if object_type in {"address", "addressgroup"}:
                navigate_url = reverse("objects") + f"?object_type=addresses&expand_id={row_id}"

            elif object_type in {"service", "servicegroup"}:
                navigate_url = reverse("objects") + f"?object_type=services&expand_id={row_id}"

            item = {
                "name": object_name,
                "row_id": row_id,
                "navigate_url": navigate_url,
                "hover_text": object_name,
            }

            if object_type in {"address", "addressgroup"}:
                if match_type == "source":
                    source_address_objects.append(item)
                elif match_type == "destination":
                    destination_address_objects.append(item)

            elif object_type in {"service", "servicegroup"}:
                if match_type == "source":
                    source_service_objects.append(item)
                elif match_type == "destination":
                    destination_service_objects.append(item)

        created_at = rule["rule_date_created"].strftime("%Y-%m-%d %H:%M") if rule["rule_date_created"] else ""

        modified_at = rule["rule_date_changed"].strftime("%Y-%m-%d %H:%M") if rule["rule_date_changed"] else ""

        rows.append(
            {
                "id": f"rule-{rule['rule_id']}",
                "is_group": False,
                "is_global": rule["rule_tenant_id"] == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, rule["rule_tenant_id"]),
                # Main row: description is no longer here.
                "cells": [
                    rule["rule_name"],
                    source_address_objects,
                    destination_address_objects,
                    source_service_objects,
                    destination_service_objects,
                    rule["rule_action"],
                    rule["rule_log_type"],
                    str(rule["rule_hit_count"]),
                    rule_tag_names,
                ],
                # Expandable row content.
                "expand": [
                    {
                        "label": "Description",
                        "value": rule["rule_description"] or "-",
                    },
                    {
                        "label": "Created",
                        "value": created_at or "-",
                    },
                    {
                        "label": "Modified",
                        "value": modified_at or "-",
                    },
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


@login_required(login_url="login")
def post_rule_view(request):
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    action = request.POST.get("action", "").strip()
    log_type = request.POST.get("log_type", "").strip()
    filter_id = request.POST.get("filter_id", "").strip()
    enable = request.POST.get("enable") == "on"

    # These values must contain typed IDs, for example:
    #
    # source_address_ids:
    #     address-1,addressgroup-2
    #
    # source_service_ids:
    #     service-3,servicegroup-4
    #
    source_address_ids_raw = request.POST.get("source_address_ids", "")
    destination_address_ids_raw = request.POST.get(
        "destination_address_ids",
        "",
    )
    source_service_ids_raw = request.POST.get("source_service_ids", "")
    destination_service_ids_raw = request.POST.get(
        "destination_service_ids",
        "",
    )

    # Keep submitted values so the modal can be rendered again after a
    # validation or processing error.
    object_data = {
        "name": name,
        "description": description,
        "action": action,
        "log_type": log_type,
        "filter_id": filter_id,
        "enable": enable,
        "source_address_ids": [value.strip() for value in source_address_ids_raw.split(",") if value.strip()],
        "destination_address_ids": [value.strip() for value in destination_address_ids_raw.split(",") if value.strip()],
        "source_service_ids": [value.strip() for value in source_service_ids_raw.split(",") if value.strip()],
        "destination_service_ids": [value.strip() for value in destination_service_ids_raw.split(",") if value.strip()],
    }

    def render_form_error(error_message: str, status: int = 400):
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": object_data,
                "error_message": error_message,
            },
            status=status,
        )

    if not all([name, action, log_type, filter_id]):
        return render_form_error("Missing required fields.")

    tenant_id_raw = request.session.get("current_tenant_id")

    if not tenant_id_raw:
        return render_form_error("Tenant not set.")

    try:
        tenant_id = int(tenant_id_raw)
    except (TypeError, ValueError):
        return render_form_error("Invalid tenant.")

    filter_obj = Filter.objects.filter(id=filter_id).first()

    if not filter_obj:
        return render_form_error(f"Filter with ID {filter_id} does not exist.")

    try:
        # Parse every selector separately.
        source_address_ordered, source_address_grouped = parse_typed_ids(source_address_ids_raw)
        destination_address_ordered, destination_address_grouped = parse_typed_ids(destination_address_ids_raw)
        source_service_ordered, source_service_grouped = parse_typed_ids(source_service_ids_raw)
        destination_service_ordered, destination_service_grouped = parse_typed_ids(destination_service_ids_raw)

        # Reject a service submitted through an address selector, and vice versa.
        validate_rule_selector_types(
            source_address_ordered,
            allowed_types=ADDRESS_OBJECT_TYPES,
            field_name="source_address_ids",
        )
        validate_rule_selector_types(
            destination_address_ordered,
            allowed_types=ADDRESS_OBJECT_TYPES,
            field_name="destination_address_ids",
        )
        validate_rule_selector_types(
            source_service_ordered,
            allowed_types=SERVICE_OBJECT_TYPES,
            field_name="source_service_ids",
        )
        validate_rule_selector_types(
            destination_service_ordered,
            allowed_types=SERVICE_OBJECT_TYPES,
            field_name="destination_service_ids",
        )

        # Bulk-fetch the selected objects separately for each selector.
        source_address_cache = fetch_objects_by_type(
            source_address_grouped,
            tenant_id,
        )
        destination_address_cache = fetch_objects_by_type(
            destination_address_grouped,
            tenant_id,
        )
        source_service_cache = fetch_objects_by_type(
            source_service_grouped,
            tenant_id,
        )
        destination_service_cache = fetch_objects_by_type(
            destination_service_grouped,
            tenant_id,
        )

        source_address_objects = build_ordered_object_list(
            source_address_ordered,
            source_address_cache,
        )
        destination_address_objects = build_ordered_object_list(
            destination_address_ordered,
            destination_address_cache,
        )
        source_service_objects = build_ordered_object_list(
            source_service_ordered,
            source_service_cache,
        )
        destination_service_objects = build_ordered_object_list(
            destination_service_ordered,
            destination_service_cache,
        )

        # If any later operation fails, do not leave a partially created Rule
        # or only some RuleMatch records in the database.
        with transaction.atomic():
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

            if source_address_objects:
                add_objects_to_rule(
                    actor=request.user,
                    tenant_id=tenant_id,
                    rule_id=new_rule.id,
                    match_type="source",
                    objects=source_address_objects,
                )

            if destination_address_objects:
                add_objects_to_rule(
                    actor=request.user,
                    tenant_id=tenant_id,
                    rule_id=new_rule.id,
                    match_type="destination",
                    objects=destination_address_objects,
                )

            # Services use "source" and "destination" as well.
            # Their model/content type tells Django that they are services.
            if source_service_objects:
                add_objects_to_rule(
                    actor=request.user,
                    tenant_id=tenant_id,
                    rule_id=new_rule.id,
                    match_type="source",
                    objects=source_service_objects,
                )

            if destination_service_objects:
                add_objects_to_rule(
                    actor=request.user,
                    tenant_id=tenant_id,
                    rule_id=new_rule.id,
                    match_type="destination",
                    objects=destination_service_objects,
                )

    except Exception as exc:
        # Prefer logging this exception with your project's logger rather than
        # exposing internal exception details to an end user.
        print(f"Error creating rule: {exc}")

        return render_form_error("Unable to create the rule. Please verify the selected objects and try again.")

    return HttpResponse(status=204)


@login_required(login_url="login")
def update_rule_view(request, rule_id):
    rule = Rule.objects.select_related("filter").filter(id=rule_id).first()

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

    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    action = request.POST.get("action", "").strip()
    log_type = request.POST.get("log_type", "").strip()
    enable = request.POST.get("enable") == "on"

    # New four-selector contract.
    source_address_ids_raw = request.POST.get("source_address_ids", "")
    destination_address_ids_raw = request.POST.get(
        "destination_address_ids",
        "",
    )
    source_service_ids_raw = request.POST.get("source_service_ids", "")
    destination_service_ids_raw = request.POST.get(
        "destination_service_ids",
        "",
    )

    # Preserve submitted form values if an error causes the modal to re-render.
    object_data = {
        "name": name,
        "description": description,
        "action": action,
        "log_type": log_type,
        "enable": enable,
        "filter_id": rule.filter_id or "",
        "source_address_ids": [value.strip() for value in source_address_ids_raw.split(",") if value.strip()],
        "destination_address_ids": [value.strip() for value in destination_address_ids_raw.split(",") if value.strip()],
        "source_service_ids": [value.strip() for value in source_service_ids_raw.split(",") if value.strip()],
        "destination_service_ids": [value.strip() for value in destination_service_ids_raw.split(",") if value.strip()],
    }

    def render_form_error(error_message: str, status: int = 400):
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "rules",
                "modal_content_partial": "partials/modals/_rule_form.html",
                "modal_supports_types": False,
                "object_data": object_data,
                "error_message": error_message,
            },
            status=status,
        )

    if not all([name, action, log_type]):
        return render_form_error("Missing required fields.")

    tenant_id_raw = request.session.get("current_tenant_id")

    if not tenant_id_raw:
        return render_form_error("Tenant not set.")

    try:
        tenant_id = int(tenant_id_raw)
    except (TypeError, ValueError):
        return render_form_error("Invalid tenant.")

    try:
        # Parse each of the four submitted selector fields.
        source_address_ordered, source_address_grouped = parse_typed_ids(source_address_ids_raw)
        destination_address_ordered, destination_address_grouped = parse_typed_ids(destination_address_ids_raw)
        source_service_ordered, source_service_grouped = parse_typed_ids(source_service_ids_raw)
        destination_service_ordered, destination_service_grouped = parse_typed_ids(destination_service_ids_raw)

        # Prevent an address selector from accepting a service typed-ID,
        # and prevent a service selector from accepting an address typed-ID.
        validate_rule_selector_types(
            source_address_ordered,
            allowed_types=ADDRESS_OBJECT_TYPES,
            field_name="source_address_ids",
        )
        validate_rule_selector_types(
            destination_address_ordered,
            allowed_types=ADDRESS_OBJECT_TYPES,
            field_name="destination_address_ids",
        )
        validate_rule_selector_types(
            source_service_ordered,
            allowed_types=SERVICE_OBJECT_TYPES,
            field_name="source_service_ids",
        )
        validate_rule_selector_types(
            destination_service_ordered,
            allowed_types=SERVICE_OBJECT_TYPES,
            field_name="destination_service_ids",
        )

        # Fetch selected address objects.
        source_address_cache = fetch_objects_by_type(
            source_address_grouped,
            tenant_id,
        )
        destination_address_cache = fetch_objects_by_type(
            destination_address_grouped,
            tenant_id,
        )

        # Fetch selected service objects.
        source_service_cache = fetch_objects_by_type(
            source_service_grouped,
            tenant_id,
        )
        destination_service_cache = fetch_objects_by_type(
            destination_service_grouped,
            tenant_id,
        )

        source_address_objects = build_ordered_object_list(
            source_address_ordered,
            source_address_cache,
        )
        destination_address_objects = build_ordered_object_list(
            destination_address_ordered,
            destination_address_cache,
        )
        source_service_objects = build_ordered_object_list(
            source_service_ordered,
            source_service_cache,
        )
        destination_service_objects = build_ordered_object_list(
            destination_service_ordered,
            destination_service_cache,
        )

        # RuleMatch.match represents direction only:
        #
        # - source
        # - destination
        #
        # The actual object type (address, addressgroup, service, or
        # servicegroup) is determined through RuleMatch.object_type.
        source_objects = source_address_objects + source_service_objects
        destination_objects = destination_address_objects + destination_service_objects

        with transaction.atomic():
            rule.name = name
            rule.description = description
            rule.action = action
            rule.log_type = log_type
            rule.enable = enable
            rule.save(
                update_fields=[
                    "name",
                    "description",
                    "action",
                    "log_type",
                    "enable",
                ]
            )

            # Call once per direction. Do NOT separately call this for
            # addresses and services if this function replaces all objects
            # for the supplied match_type.
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

    except Exception as exc:
        print(f"Error updating rule {rule_id}: {exc}")

        return render_form_error("Unable to update the rule. Please verify the selected objects and try again.")

    return HttpResponse(status=204)


@login_required(login_url="login")
def delete_rule_view(request, rule_id):
    tenant_id_raw = request.session.get("current_tenant_id")

    if not tenant_id_raw:
        return HttpResponse("No tenant selected.", status=400)

    try:
        tenant_id = int(tenant_id_raw)

        delete_rule(
            actor=request.user,
            tenant_id=tenant_id,
            rule_id=rule_id,
        )

    except Exception as exc:
        return HttpResponse(
            f"Could not delete rule: {exc}",
            status=400,
        )

    return HttpResponse(status=204)


@login_required(login_url="login")
def get_rule_selector_modal(request, selector_type: str):
    """
    Render one of four rule-object selectors:

    - source_address
    - destination_address
    - source_service
    - destination_service
    """

    address_selector_types = {
        "source_address",
        "destination_address",
    }

    service_selector_types = {
        "source_service",
        "destination_service",
    }

    supported_selector_types = address_selector_types | service_selector_types

    if selector_type not in supported_selector_types:
        return HttpResponseBadRequest(f"Unsupported rule selector type: {selector_type!r}")

    selected_ids_raw = request.GET.get("selected_ids", "")

    # These must be typed IDs, such as:
    # address-1,addressgroup-4
    # service-3,servicegroup-2
    selected_object_ids = {value.strip() for value in selected_ids_raw.split(",") if value.strip()}

    if selector_type in address_selector_types:
        item_options = get_item_options_view(request, "addresses")
        group_options = get_group_options_view(request, "addresses")

        for item in item_options:
            item["selector_id"] = f"address-{item['id']}"

        for group in group_options:
            group["selector_id"] = f"addressgroup-{group['id']}"

        object_kind = "addresses"

    else:
        item_options = get_item_options_view(request, "services")
        group_options = get_group_options_view(request, "services")

        for item in item_options:
            item["selector_id"] = f"service-{item['id']}"

        for group in group_options:
            group["selector_id"] = f"servicegroup-{group['id']}"

        object_kind = "services"

    context = {
        "modal_title": f"Edit {selector_type.replace('_', ' ').title()}",
        "modal_mode": "submodal",
        "modal_object_type": "rule-selector",
        "modal_content_partial": "partials/modals/_rule_selector_modal.html",
        "modal_instance_id": f"submodal-{selector_type}",
        "modal_is_submodal": True,
        # The exact four-way selector identifier.
        "selector_type": selector_type,
        # Useful for text and client-side behavior.
        "object_kind": object_kind,
        # A set enables clean `in selected_object_ids` comparisons in template.
        "selected_object_ids": selected_object_ids,
        "item_options": item_options,
        "group_options": group_options,
    }

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


def validate_rule_selector_types(
    ordered_ids: list[tuple[str, int]],
    allowed_types: set[str],
    field_name: str,
) -> None:
    invalid_types = {object_type for object_type, _object_id in ordered_ids if object_type not in allowed_types}

    if invalid_types:
        formatted_types = ", ".join(sorted(invalid_types))

        raise ValueError(f"Invalid object type(s) in {field_name}: {formatted_types}")
