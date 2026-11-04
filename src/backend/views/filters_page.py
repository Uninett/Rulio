from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from backend.objects.attributes.tag import Tag
from backend.objects.draft import Draft
from backend.objects.filters.rule import Rule
from backend.services.filter_draft import (
    FilterDraftError,
    apply_filter_draft,
    build_filter_changeset,
    discard_filter_draft,
    filter_changes_pending,
    filter_delete_counts,
    get_filter_changes,
    load_baseline_filters,
    parse_filter_form,
    stage_filter_create,
    stage_filter_delete,
    stage_filter_update,
)
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.rule_draft import RULE_DRAFT_SCOPE, empty_rule_changes, rule_changes_pending
from backend.views.search import get_global_search_results
from backend.views.session import get_tenant_context
from constants import GLOBAL_TENANT_ID

"""
====================================================================
Filters Page
====================================================================
"""


@login_required(login_url="login")
def get_filters_page(request):
    request.session["active_page"] = "filters"
    return render(
        request,
        "filters.html",
        {
            "active_page": "filters",
            "page_title": "Filters",
            "object_type": "filters",
            "object_extra_type": "rules",
            "add_button_label": "Add Filter",
            "filters": get_filters_view(request),  # Address data for the page
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )


@login_required(login_url="login")
def get_filters_content(request):
    request.session["active_page"] = "filters"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Filters",
            "page_title": "Filters",
            "object_type": "filters",
            "object_extra_type": "rules",
            "add_button_label": "Add Filter",
            "filters": get_filters_view(request),
            **get_tenant_context(request),
        },
    )


# The saved value of a changed cell, shown as a tooltip while differences are shown. None if the field is unchanged.
def _object_change_summary(*, added=(), removed=(), changed=()) -> str:
    return "; ".join(
        f"{label}: {', '.join(names)}"
        for label, names in (("Added", added), ("Removed", removed), ("Changed", changed))
        if names
    )


def _filter_previous_value(entry: dict, field: str, tags_by_id: dict) -> str | None:
    if field not in entry["changed_fields"]:
        return None

    value = entry["previous_fields"][field]
    if field == "tag_ids":
        current = entry["fields"][field]
        return _object_change_summary(
            added=[tags_by_id[tag_id].name for tag_id in current if tag_id not in value and tag_id in tags_by_id],
            removed=[tags_by_id[tag_id].name for tag_id in value if tag_id not in current and tag_id in tags_by_id],
        )
    return f"(Was: {value or 'none'})"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


# What saving a removed filter also deletes, or None when nothing else is deleted.
def _filter_delete_note(filter_id: int) -> str | None:
    rule_count, interface_count = filter_delete_counts(filter_id)
    parts = []
    if rule_count:
        parts.append(f"deletes its {_plural(rule_count, 'rule')}")
    if interface_count:
        parts.append(f"removes it from {_plural(interface_count, 'interface')}")
    return f"Saving {' and '.join(parts)}." if parts else None


# One table row for a changeset entry. saved_filter is the baseline filter, or None for a filter only created
# in the draft.
def _filter_row(entry: dict, saved_filter: dict | None, user, tenant_id: int, tags_by_id: dict) -> dict:
    fields = entry["fields"]
    filter_tenant_id = saved_filter["tenant_id"] if saved_filter else tenant_id
    is_removed = entry["status"] == "removed"

    diff_classes = {
        "added": "row-diff-added",
        "removed": "row-diff-removed",
        "changed": "row-diff-changed",
    }.get(entry["status"], "")

    tags = [tags_by_id[tag_id] for tag_id in fields["tag_ids"] if tag_id in tags_by_id]
    # A filter only created in the draft has no rules yet.
    rule_names = ", ".join(saved_filter["rule_names"]) if saved_filter else ""

    expand = [
        {"label": "Rules", "value": rule_names},
        {"label": "Tags", "value": tags},
    ]
    change_notes = []
    for field, label in (("name", "Name"), ("description", "Description"), ("tag_ids", "Tags")):
        previous = _filter_previous_value(entry, field, tags_by_id)
        if previous is not None:
            change_notes.append({"label": label, "value": previous})
    if is_removed:
        delete_note = _filter_delete_note(saved_filter["filter_id"])
        if delete_note:
            expand.append({"label": "Unsaved deletion", "value": delete_note})

    return {
        "id": entry["key"],
        "is_group": False,
        # Only saved filters open the rules page, since a filter created in the draft has no id yet.
        "inspect_url": reverse("rules-page", kwargs={"filter_id": saved_filter["filter_id"]})
        if saved_filter and not is_removed
        else None,
        "is_global": filter_tenant_id == GLOBAL_TENANT_ID,
        "can_write": can_write_tenant(user, filter_tenant_id) and not is_removed,
        "is_removed": is_removed,
        "diff_classes": diff_classes,
        "cells": [fields["name"], fields["description"], rule_names, tags],
        "was": [
            _filter_previous_value(entry, "name", tags_by_id),
            _filter_previous_value(entry, "description", tags_by_id),
            None,
            _filter_previous_value(entry, "tag_ids", tags_by_id),
        ],
        "expand": expand,
        "change_notes": change_notes,
    }


def get_filters_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {"headers": [], "rows": [], "has_changes": False}

    tenant_id = int(tenant_id)

    # A user who can't read the tenant sees an empty table.
    try:
        baseline = load_baseline_filters(request.user, tenant_id)
    except PermissionDenied as e:
        print(f"Error fetching filters: {e}")
        return {"headers": [], "rows": [], "has_changes": False}

    # The rows show the saved filters with this user's unsaved changes applied.
    changes = get_filter_changes(request.user, tenant_id)
    changeset = build_filter_changeset(baseline, changes)
    baseline_by_key = {row["key"]: row for row in baseline}

    # Loads the tags of every filter at once, including the previous tags of changed filters.
    tag_ids = {
        tag_id
        for entry in changeset
        for fields in (entry["fields"], entry["previous_fields"] or {})
        for tag_id in fields.get("tag_ids", [])
    }
    tags_by_id = {tag.id: tag for tag in Tag.objects.filter(id__in=tag_ids)}

    # Every row, also new and removed ones, is placed by its current name, as it will be after saving.
    changeset = sorted(changeset, key=lambda entry: entry["fields"]["name"].lower())
    rows = [
        _filter_row(entry, baseline_by_key.get(entry["key"]), request.user, tenant_id, tags_by_id)
        for entry in changeset
    ]
    pending_rule_drafts = {
        f"filter-{draft.scope_id}": {**empty_rule_changes(), **draft.changes}
        for draft in Draft.objects.filter(
            user=request.user,
            tenant_id=tenant_id,
            scope=RULE_DRAFT_SCOPE,
            scope_id__in=[row["filter_id"] for row in baseline],
        ).only("scope_id", "changes")
        if rule_changes_pending({**empty_rule_changes(), **draft.changes})
    }
    rule_names_by_key = {
        f"rule-{rule.id}": rule.name
        for rule in Rule.objects.filter(filter_id__in=[int(key.split("-", 1)[1]) for key in pending_rule_drafts])
    }
    for row in rows:
        rule_changes = pending_rule_drafts.get(row["id"])
        if rule_changes is None:
            continue
        if not row["diff_classes"]:
            row["diff_classes"] = "row-diff-changed"
        changed_keys = dict.fromkeys(
            [
                *rule_changes["updated"],
                *rule_changes["created"],
                *rule_changes["deleted"],
                *(rule_changes["moved"] or (rule_changes["order"] or [])),
            ]
        )
        names_by_status = {"added": [], "removed": [], "changed": []}
        for key in changed_keys:
            if key in rule_changes["deleted"]:
                status = "removed"
                fields = {}
            elif key in rule_changes["created"]:
                status = "added"
                fields = rule_changes["created"][key]
            else:
                status = "changed"
                fields = rule_changes["updated"].get(key, {})
            name = fields.get("name") or rule_names_by_key.get(key)
            if name:
                names_by_status[status].append(name)
        summary = _object_change_summary(**names_by_status)
        if summary:
            row["change_notes"].append({"label": "Rules", "value": summary})
            row["was"][2] = summary

    return {
        "headers": ["Name", "Description", "Rules", "Tags"],
        "rows": rows,
        "has_changes": filter_changes_pending(changes),
    }


def _render_filter_form_error(request, object_data: dict, error_message: str, status: int = 400):
    return render(
        request,
        "partials/modals/_modal_form.html",
        {
            "modal_object_type": "filters",
            "modal_content_partial": "partials/modals/_filter_form.html",
            "modal_supports_types": False,
            "object_data": object_data,
            "error_message": error_message,
        },
        status=status,
    )


# Adding a filter only stages it in the user's draft. It is written to the database when the draft is saved.
@login_required(login_url="login")
def post_filter_view(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    object_data = {}

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return _render_filter_form_error(request, object_data, "Tenant not set.")

    try:
        fields = parse_filter_form(request.POST)
        object_data.update(fields)

        stage_filter_create(actor=request.user, tenant_id=int(tenant_id_raw), fields=fields)
    except (FilterDraftError, PermissionDenied) as exc:
        return _render_filter_form_error(request, object_data, str(exc))

    return HttpResponse(status=204)


# row_key is "filter-<id>" for a saved filter or "filterdraft-<n>" for a filter only created in the draft.
@login_required(login_url="login")
def update_filter_view(request, row_key):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    object_data = {}

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return _render_filter_form_error(request, object_data, "Tenant not set.")

    try:
        fields = parse_filter_form(request.POST)
        object_data.update(fields)

        stage_filter_update(actor=request.user, tenant_id=int(tenant_id_raw), key=row_key, fields=fields)
    except (FilterDraftError, PermissionDenied) as exc:
        return _render_filter_form_error(request, object_data, str(exc))

    return HttpResponse(status=204)


# Deleting only stages the deletion in the user's draft. A filter only created in the draft is dropped from it.
@login_required(login_url="login")
def delete_filter_view(request, row_key):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    tenant_id_raw = request.session.get("current_tenant_id")

    if not tenant_id_raw:
        return HttpResponse("No tenant selected.", status=400)

    try:
        stage_filter_delete(actor=request.user, tenant_id=int(tenant_id_raw), key=row_key)
    except (FilterDraftError, PermissionDenied) as exc:
        return HttpResponse(f"Could not delete filter: {exc}", status=400)

    return HttpResponse(status=204)


# Writes the user's filter draft to the database. On any error nothing is saved and the draft is kept.
@login_required(login_url="login")
def save_filter_draft_view(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return HttpResponse("No tenant selected.", status=400)

    try:
        apply_filter_draft(actor=request.user, tenant_id=int(tenant_id_raw))
    except (ValueError, PermissionDenied) as exc:
        return HttpResponse(f"Could not save filter changes: {exc}", status=400)

    return HttpResponse(status=204)


# Throws away the user's filter draft, so the filters page shows the saved filters again.
@login_required(login_url="login")
def discard_filter_draft_view(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    tenant_id_raw = request.session.get("current_tenant_id")
    if not tenant_id_raw:
        return HttpResponse("No tenant selected.", status=400)

    discard_filter_draft(request.user, int(tenant_id_raw))
    return HttpResponse(status=204)
