from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.services.delete import delete_rule, remove_tag_from_object
from backend.services.filter_objects.create_filter_objects import create_rule
from backend.services.get import (
    get_all_rules_with_objects_from_filter,
    get_all_tags_from_object,
)
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.membership import (
    add_objects_to_rule,
    add_tag_to_object,
    update_objects_in_rule,
)
from backend.services.rule_draft import (
    RULE_OBJECT_FIELDS,
    RuleDraftError,
    apply_rule_draft,
    build_rule_changeset,
    discard_rule_draft,
    get_rule_changes,
    load_baseline_rules,
    parse_rule_form,
    rule_changes_pending,
    stage_rule_create,
    stage_rule_delete,
    stage_rule_enable_toggle,
    stage_rule_order,
    stage_rule_update,
)
from backend.services.update import update_rule_sequence
from backend.views.modal import get_group_options_view, get_item_options_view
from backend.views.session import get_tenant_context
from constants import GLOBAL_TENANT_ID

ADDRESS_OBJECT_TYPES = {"address", "addressgroup"}
SERVICE_OBJECT_TYPES = {"service", "servicegroup"}


"""
====================================================================
Rule Page
====================================================================
"""


@login_required(login_url="login")
def get_rule_page(request, filter_id):
    filter_name = getattr(Filter.objects.filter(id=filter_id).first(), "name", "")
    breadcrumbs = [
        {"label": "Filters", "url": reverse("filters")},
        {"label": filter_name, "url": f"{reverse('filters')}?expand_id=filter-{filter_id}"},
        {"label": "Rules", "url": None},
    ]

    request.session["active_page"] = "Filters"
    return render(
        request,
        "rules.html",
        {
            "active_page": "Filters",
            "page_title": "Rules",
            "breadcrumbs": breadcrumbs,
            "object_type": "rules",
            "add_button_label": "Add Rule",
            "current_filter_id": filter_id,
            "current_filter_name": filter_name,
            "rules": get_rules_view(request, filter_id),
            **get_tenant_context(request),
        },
    )


@login_required(login_url="login")
def get_rules_content(request, filter_id):
    filter_name = getattr(Filter.objects.filter(id=filter_id).first(), "name", "")
    breadcrumbs = [
        {"label": "Filters", "url": reverse("filters")},
        {"label": filter_name, "url": f"{reverse('filters')}?expand_id=filter-{filter_id}"},
        {"label": "Rules", "url": None},
    ]

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Rules",
            "page_title": "Rules",
            "breadcrumbs": breadcrumbs,
            "object_type": "rules",
            "add_button_label": "Add Rule",
            "current_filter_id": filter_id,
            "current_filter_name": filter_name,
            "rules": get_rules_view(request, filter_id),
            **get_tenant_context(request),
        },
    )


# Loads the objects and tags of every rule in the changeset at once, including the previous values of changed rules.
def _load_rule_display_objects(changeset: list[dict], tenant_id: int):
    typed_ids = set()
    tag_ids = set()
    for entry in changeset:
        for fields in (entry["fields"], entry["previous_fields"] or {}):
            for field in RULE_OBJECT_FIELDS:
                typed_ids.update(fields.get(field, []))
            tag_ids.update(fields.get("tag_ids", []))

    _ordered, grouped = parse_typed_ids(",".join(typed_ids))
    objects_by_type = fetch_objects_by_type(grouped, tenant_id)
    tags_by_id = {tag.id: tag for tag in Tag.objects.filter(id__in=tag_ids)}
    return objects_by_type, tags_by_id


# The object links shown in a rule's Src/Dst columns. Objects that no longer exist are left out.
def _rule_object_items(typed_ids: list[str], objects_by_type: dict) -> list[dict]:
    items = []
    for typed_id in typed_ids:
        object_type, object_id = typed_id.split("-", 1)
        obj = objects_by_type.get(object_type, {}).get(int(object_id))
        if obj is None:
            continue

        object_kind = "addresses" if object_type in ADDRESS_OBJECT_TYPES else "services"
        items.append(
            {
                "name": obj.name,
                "row_id": typed_id,
                "navigate_url": reverse("objects") + f"?object_type={object_kind}&expand_id={typed_id}",
                "hover_text": obj.name,
            }
        )
    return items

 
# The saved value of a changed cell, shown as a tooltip while differences are shown. None if the field is unchanged.
def _rule_previous_value(entry: dict, field: str, objects_by_type: dict, tags_by_id: dict) -> str | None:
    if field not in entry["changed_fields"]:
        return None

    value = entry["previous_fields"][field]
    if field in RULE_OBJECT_FIELDS:
        text = ", ".join(item["name"] for item in _rule_object_items(value, objects_by_type))
    elif field == "tag_ids":
        text = ", ".join(tags_by_id[tag_id].name for tag_id in value if tag_id in tags_by_id)
    else:
        text = value
    return f"Was: {text or 'none'}"


# kind tells _ruleRow.html how to render the cell: sequence, text, objects, enable or tags.
def _rule_cell(kind: str, value, previous: str | None = None) -> dict:
    return {"kind": kind, "value": value, "was": previous}


# One table row for a changeset entry. saved_rule is the baseline rule, or None for a rule only created in the draft.
def _rule_row(entry: dict, saved_rule: dict | None, user, tenant_id: int, objects_by_type: dict, tags_by_id: dict):
    fields = entry["fields"]
    rule_tenant_id = saved_rule["tenant_id"] if saved_rule else tenant_id
    is_removed = entry["status"] == "removed"

    def previous(field):
        return _rule_previous_value(entry, field, objects_by_type, tags_by_id)

    diff_classes = ""
    if entry["status"] == "added":
        diff_classes = "row-diff-added"
    elif is_removed:
        diff_classes = "row-diff-removed"
    elif entry["enable_changed"]:
        # Enabling and disabling count as an addition and a deletion, so they take precedence over yellow.
        diff_classes = "row-diff-enabled-on" if fields["enable"] else "row-diff-enabled-off"
    elif entry["status"] == "changed":
        diff_classes = "row-diff-changed"

    if saved_rule:
        created_at = saved_rule["date_created"].strftime("%Y-%m-%d %H:%M") if saved_rule["date_created"] else ""
        modified_at = saved_rule["date_changed"].strftime("%Y-%m-%d %H:%M") if saved_rule["date_changed"] else ""
    else:
        created_at = modified_at = "Not saved yet"

    # The description is only shown in the details row, so its previous value is shown there too.
    description = fields["description"] or "-"
    if "description" in entry["changed_fields"]:
        description = f"{description} (was: {entry['previous_fields']['description'] or '-'})"

    return {
        "id": entry["key"],
        "is_group": False,
        "is_global": rule_tenant_id == GLOBAL_TENANT_ID,
        "can_write": can_write_tenant(user, rule_tenant_id) and not is_removed,
        "is_removed": is_removed,
        "diff_classes": diff_classes,
        "enable_was": f"Was: {'Enabled' if entry['previous_fields']['enable'] else 'Disabled'}"
        if entry["enable_changed"]
        else None,
        # Main row: description is no longer here.
        "cells": [
            _rule_cell(
                "sequence",
                {"current": entry["sequence"], "previous": entry["previous_sequence"], "moved": entry["moved"]},
            ),
            _rule_cell("text", fields["name"], previous("name")),
            *(
                _rule_cell("objects", _rule_object_items(fields[field], objects_by_type), previous(field))
                for field in RULE_OBJECT_FIELDS
            ),
            _rule_cell("text", fields["action"], previous("action")),
            _rule_cell("text", fields["log_type"], previous("log_type")),
            _rule_cell("text", str(saved_rule["hit_count"]) if saved_rule else "0"),
            _rule_cell("enable", fields["enable"]),
            _rule_cell("tags", [tags_by_id[tag_id] for tag_id in fields["tag_ids"] if tag_id in tags_by_id], previous("tag_ids")),
        ],
        # Expandable row content.
        "expand": [
            {"label": "Description", "value": description},
            {"label": "Created", "value": created_at or "-"},
            {"label": "Modified", "value": modified_at or "-"},
        ],
    }


def get_rules_view(request, filter_id):
    tenant_id = request.session.get("current_tenant_id")

    if not tenant_id:
        return {"headers": [], "rows": [], "has_changes": False}

    tenant_id = int(tenant_id)

    # Description, Created, and Modified have moved to the expandable section.
    headers = [
        "Seq",
        "Name",
        "Src-Address",
        "Dst-Address",
        "Src-Service",
        "Dst-Service",
        "Action",
        "Log",
        "Count",
        "Enabled",
        "Tags",
    ]

    if not filter_id:
        return {"headers": headers, "rows": [], "has_changes": False}

    try:
        baseline = load_baseline_rules(request.user, tenant_id, int(filter_id))
    except Exception as exc:
        print(f"Error fetching rules with objects for filter {filter_id}: {exc}")
        return {"headers": headers, "rows": [], "has_changes": False}

    # The rows show the saved rules with this user's unsaved changes applied.
    changes = get_rule_changes(request.user, int(filter_id))
    changeset = build_rule_changeset(baseline, changes)
    baseline_by_key = {rule["key"]: rule for rule in baseline}
    objects_by_type, tags_by_id = _load_rule_display_objects(changeset, tenant_id)

    rows = [
        _rule_row(entry, baseline_by_key.get(entry["key"]), request.user, tenant_id, objects_by_type, tags_by_id)
        for entry in changeset
    ]

    return {
        "headers": headers,
        "rows": rows,
        "has_changes": rule_changes_pending(changes),
    }


def _render_rule_form_error(request, object_data: dict, error_message: str, status: int = 400):
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


# Adding a rule only stages it in the user's draft. It is written to the database when the draft is saved.
@login_required(login_url="login")
def post_rule_view(request):
    filter_id = request.POST.get("filter_id", "").strip()
    object_data = {"filter_id": filter_id}

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return _render_rule_form_error(request, object_data, "Tenant not set.")

    try:
        fields = parse_rule_form(request.POST)
        object_data.update(fields)

        if not Filter.objects.filter(id=filter_id).exists():
            return _render_rule_form_error(request, object_data, f"Filter with ID {filter_id} does not exist.")

        stage_rule_create(actor=request.user, tenant_id=int(tenant_id_raw), filter_id=int(filter_id), fields=fields)
    except (RuleDraftError, PermissionDenied) as exc:
        return _render_rule_form_error(request, object_data, str(exc))
    except (TypeError, ValueError):
        return _render_rule_form_error(request, object_data, "Invalid tenant or filter.")

    return HttpResponse(status=204)


@login_required(login_url="login")
@transaction.atomic
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

    source_address_ids_raw = request.POST.get("source_address_ids", "")
    destination_address_ids_raw = request.POST.get("destination_address_ids", "")
    source_service_ids_raw = request.POST.get("source_service_ids", "")
    destination_service_ids_raw = request.POST.get("destination_service_ids", "")

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

        # Added: selected tag IDs from the form.
        submitted_tag_ids = {int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id}
    except (TypeError, ValueError):
        return render_form_error("Invalid tenant or tag selection.")

    try:
        source_address_ordered, source_address_grouped = parse_typed_ids(source_address_ids_raw)
        destination_address_ordered, destination_address_grouped = parse_typed_ids(destination_address_ids_raw)
        source_service_ordered, source_service_grouped = parse_typed_ids(source_service_ids_raw)
        destination_service_ordered, destination_service_grouped = parse_typed_ids(destination_service_ids_raw)

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

        source_address_objects = build_ordered_object_list(
            source_address_ordered,
            fetch_objects_by_type(source_address_grouped, tenant_id),
        )
        destination_address_objects = build_ordered_object_list(
            destination_address_ordered,
            fetch_objects_by_type(destination_address_grouped, tenant_id),
        )
        source_service_objects = build_ordered_object_list(
            source_service_ordered,
            fetch_objects_by_type(source_service_grouped, tenant_id),
        )
        destination_service_objects = build_ordered_object_list(
            destination_service_ordered,
            fetch_objects_by_type(destination_service_grouped, tenant_id),
        )

        source_objects = source_address_objects + source_service_objects
        destination_objects = destination_address_objects + destination_service_objects

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

        # Added: synchronize tag assignments.
        current_tags = get_all_tags_from_object(
            actor=request.user,
            tenant_id=tenant_id,
            object_id=rule.id,
            object_type="rule",
        )
        current_tag_ids = {tag.id for tag in current_tags}

        for tag_id in submitted_tag_ids - current_tag_ids:
            tag = Tag.objects.get(
                id=tag_id,
                tenant_id__in=[tenant_id, GLOBAL_TENANT_ID],
            )
            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=rule,
            )

        for tag_id in current_tag_ids - submitted_tag_ids:
            remove_tag_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_id=rule.id,
                object_type="rule",
                tag_id=tag_id,
            )

    except Exception as exc:
        print(f"Error updating rule {rule_id}: {exc}")
        return render_form_error("Unable to update the rule. Please verify the selected objects and tags.")

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
def reorder_rule_view(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return HttpResponse("No tenant selected.", status=400)

    rule_id_raw = request.POST.get("rule_id")
    filter_id_raw = request.POST.get("filter_id")
    new_sequence_raw = request.POST.get("new_sequence")

    if not all([rule_id_raw, filter_id_raw, new_sequence_raw]):
        return HttpResponse("Missing rule reorder data.", status=400)

    try:
        tenant_id = int(tenant_id_raw)
        rule_id = int(rule_id_raw)
        filter_id = int(filter_id_raw)
        new_sequence = int(new_sequence_raw)
    except (TypeError, ValueError):
        return HttpResponse("Invalid rule reorder data.", status=400)

    rule = Rule.objects.select_related("filter").filter(id=rule_id, tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).first()
    if not rule:
        return HttpResponse("Rule not found.", status=404)

    if rule.filter_id != filter_id:
        return HttpResponse("Rule does not belong to the requested filter.", status=400)

    try:
        update_rule_sequence(
            actor=request.user,
            tenant_id=tenant_id,
            rule=rule,
            new_sequence=new_sequence,
        )
    except Exception as exc:
        return HttpResponse(f"Could not reorder rule: {exc}", status=400)

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
