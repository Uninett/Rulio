from django.core.exceptions import ValidationError
from django.db import transaction

from backend.objects.attributes.tag import Tag
from backend.objects.draft import Draft
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.services.delete import delete_filter, remove_tag_from_object
from backend.services.draft import (
    DraftError,
    build_changeset,
    changes_pending,
    discard_draft,
    get_changes,
    get_draft,
    require_editable_row,
    require_rows_still_exist,
    saved_key,
    set_row_fields,
    stage_create,
    stage_delete,
    store_changes,
)
from backend.services.filter_objects.create_filter_objects import create_filter
from backend.services.get import get_all_tags_from_object
from backend.services.helper_user_tenant import (
    require_read_tenant,
    require_write_tenant,
)
from backend.services.membership import add_tag_to_object
from backend.services.rule_draft import RULE_DRAFT_SCOPE
from backend.services.update import update_filter
from constants import GLOBAL_TENANT_ID

# Pending filter changes are stored in one Draft per (user, tenant), under this scope.
# The filters page isn't tied to one object, so the scope id is always 0.
FILTER_DRAFT_SCOPE = "filters"
FILTER_DRAFT_SCOPE_ID = 0

FILTER_FIELDS = ("name", "description", "tag_ids")


# The same class as DraftError, so `except FilterDraftError` also catches errors raised in backend.services.draft.
FilterDraftError = DraftError


"""
====================================================================
Filter Form
====================================================================
"""


# Reads the filter modal form into a fields dict.
def parse_filter_form(post) -> dict:
    try:
        # Sorted, so the same selection always compares equal.
        tag_ids = sorted({int(tag_id) for tag_id in post.getlist("tag_ids") if tag_id})
    except (TypeError, ValueError):
        raise FilterDraftError("Invalid tag selection.")

    return {
        "name": post.get("name", "").strip(),
        "description": post.get("description", "").strip(),
        "tag_ids": tag_ids,
    }


# Checks a filter before it goes into the draft, so problems are shown in the modal instead of when saving.
# filter_tenant_id is the tenant of the saved filter being edited, or None for a new filter (made in tenant_id).
def validate_filter_fields(fields: dict, tenant_id: int, filter_tenant_id: int | None = None) -> None:
    if not fields["name"]:
        raise FilterDraftError("Missing required fields.")

    # Checked here, since a longer name would only fail in the database when the draft is saved.
    max_name_length = Filter._meta.get_field("name").max_length
    if len(fields["name"]) > max_name_length:
        raise FilterDraftError(f"The name can be at most {max_name_length} characters.")

    found_tags = Tag.objects.filter(id__in=fields["tag_ids"], tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).count()
    if found_tags != len(fields["tag_ids"]):
        raise FilterDraftError("Invalid tag selection.")

    # A tag must be global or in the filter's own tenant, so a global filter can't have tenant tags.
    if (
        filter_tenant_id == GLOBAL_TENANT_ID
        and Tag.objects.filter(id__in=fields["tag_ids"]).exclude(tenant_id=GLOBAL_TENANT_ID).exists()
    ):
        raise FilterDraftError("A global filter can only have global tags.")


"""
====================================================================
Writing Filters
====================================================================
"""


# Adds and removes tags so the filter has exactly tag_ids.
def write_filter_tags(*, actor, tenant_id: int, filter_obj: Filter, tag_ids: list[int]) -> None:
    current_tags = get_all_tags_from_object(
        actor=actor, tenant_id=tenant_id, object_id=filter_obj.id, object_type="filter"
    )
    current_tag_ids = {tag.id for tag in current_tags}
    submitted_tag_ids = set(tag_ids)

    tags_to_add = list(
        Tag.objects.filter(id__in=submitted_tag_ids - current_tag_ids, tenant_id__in=[tenant_id, GLOBAL_TENANT_ID])
    )
    # A tag deleted since the change was staged, stops the save, so the filter isn't saved without it.
    if len(tags_to_add) != len(submitted_tag_ids - current_tag_ids):
        raise FilterDraftError("A selected tag no longer exists. Edit the filter and save again.")

    for tag in tags_to_add:
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag, obj=filter_obj)

    for tag_id in current_tag_ids - submitted_tag_ids:
        remove_tag_from_object(
            actor=actor,
            tenant_id=tenant_id,
            object_id=filter_obj.id,
            object_type="filter",
            tag_id=tag_id,
        )


"""
====================================================================
Baseline (the saved filters)
====================================================================
"""


# Filters are identified by row key: "filter-<id>" for saved filters and "filterdraft-<n>" for filters created
# in the draft.
def saved_filter_key(filter_id: int) -> str:
    return saved_key("filter", filter_id)


# The saved filters the tenant can see (its own and the global ones), with their fields in the same format as
# parse_filter_form, so they can be compared. rule_names only holds the rules the tenant can see.
def load_baseline_filters(actor, tenant_id: int) -> list[dict]:
    require_read_tenant(actor, tenant_id)
    visible_tenant_ids = [tenant_id, GLOBAL_TENANT_ID]

    filters = list(
        Filter.objects.filter(tenant_id__in=visible_tenant_ids).prefetch_related("tag_objects").order_by("id")
    )

    rule_names_by_filter = {}
    for filter_id, rule_name in Rule.objects.filter(
        filter_id__in=[filter_obj.id for filter_obj in filters], tenant_id__in=visible_tenant_ids
    ).values_list("filter_id", "name"):
        rule_names_by_filter.setdefault(filter_id, []).append(rule_name)

    return [
        {
            "key": saved_filter_key(filter_obj.id),
            "filter_id": filter_obj.id,
            "tenant_id": filter_obj.tenant_id,
            "rule_names": sorted(rule_names_by_filter.get(filter_obj.id, []), key=str.lower),
            "fields": {
                "name": filter_obj.name,
                "description": filter_obj.description or "",
                "tag_ids": sorted({tag_object.tag_id for tag_object in filter_obj.tag_objects.all()}),
            },
        }
        for filter_obj in filters
    ]


# What deleting a filter also deletes: all its rules and interface links, including ones other tenants own.
def filter_delete_counts(filter_id: int) -> tuple[int, int]:
    rule_count = Rule.objects.filter(filter_id=filter_id).count()
    interface_count = FilterInterface.objects.filter(filter_id=filter_id).count()
    return rule_count, interface_count


"""
====================================================================
Draft Storage
====================================================================
"""


def get_filter_draft(actor, tenant_id: int) -> Draft | None:
    return get_draft(actor, tenant_id, FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID)


def get_filter_changes(actor, tenant_id: int) -> dict:
    return get_changes(actor, tenant_id, FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID)


def filter_changes_pending(changes: dict) -> bool:
    return changes_pending(changes)


def _store_filter_changes(actor, tenant_id: int, changes: dict) -> None:
    store_changes(actor, tenant_id, FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID, changes)


def discard_filter_draft(actor, tenant_id: int) -> None:
    discard_draft(actor, tenant_id, FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID)


def _load_filter_state(actor, tenant_id: int):
    baseline = load_baseline_filters(actor, tenant_id)
    baseline_by_key = {row["key"]: row for row in baseline}
    return baseline, baseline_by_key, get_filter_changes(actor, tenant_id)


"""
====================================================================
Staging Changes
====================================================================
"""


def stage_filter_create(*, actor, tenant_id: int, fields: dict) -> str:
    require_write_tenant(actor, tenant_id)
    _baseline, _baseline_by_key, changes = _load_filter_state(actor, tenant_id)

    validate_filter_fields(fields, tenant_id)
    key = stage_create(changes, "filter", fields)

    _store_filter_changes(actor, tenant_id, changes)
    return key


def stage_filter_update(*, actor, tenant_id: int, key: str, fields: dict) -> None:
    require_write_tenant(actor, tenant_id)
    _baseline, baseline_by_key, changes = _load_filter_state(actor, tenant_id)
    require_editable_row(actor, key, baseline_by_key, changes, "filter")

    saved_filter = baseline_by_key.get(key)
    validate_filter_fields(fields, tenant_id, saved_filter["tenant_id"] if saved_filter else None)
    set_row_fields(key, fields, baseline_by_key, changes)

    _store_filter_changes(actor, tenant_id, changes)


def stage_filter_delete(*, actor, tenant_id: int, key: str) -> None:
    require_write_tenant(actor, tenant_id)
    _baseline, baseline_by_key, changes = _load_filter_state(actor, tenant_id)
    require_editable_row(actor, key, baseline_by_key, changes, "filter")

    stage_delete(changes, key)
    _store_filter_changes(actor, tenant_id, changes)


"""
====================================================================
Changeset (the differences between the saved filters and the draft)
====================================================================
"""


# One entry per filter: the saved filters, then the ones created in the draft. The page sorts them by name.
def build_filter_changeset(baseline: list[dict], changes: dict) -> list[dict]:
    return build_changeset(baseline, changes, FILTER_FIELDS)


"""
====================================================================
Saving
====================================================================
"""


# Writes the whole draft in one transaction, so either every change is saved or none are.
@transaction.atomic
def apply_filter_draft(*, actor, tenant_id: int) -> None:
    require_write_tenant(actor, tenant_id)

    draft = get_filter_draft(actor, tenant_id)
    if draft is None:
        return

    _baseline, baseline_by_key, changes = _load_filter_state(actor, tenant_id)
    require_rows_still_exist(actor, changes, baseline_by_key, "filter")

    # A model check that fails while writing (e.g. a tag in the wrong tenant) is shown to the user. Raising it
    # still rolls back the transaction, so nothing is saved and the draft is kept.
    try:
        for key in changes["deleted"]:
            row = baseline_by_key[key]
            # Deleted in the filter's own tenant, so a superuser can delete a global filter from any tenant.
            delete_filter(actor, row["tenant_id"], row["filter_id"])
            # The filter's rules are gone, so every user's unsaved rule changes for it are too.
            Draft.objects.filter(scope=RULE_DRAFT_SCOPE, scope_id=row["filter_id"]).delete()

        for key, fields in changes["updated"].items():
            filter_obj = update_filter(
                actor=actor,
                tenant_id=tenant_id,
                filter_id=baseline_by_key[key]["filter_id"],
                name=fields["name"],
                description=fields["description"],
            )
            write_filter_tags(actor=actor, tenant_id=tenant_id, filter_obj=filter_obj, tag_ids=fields["tag_ids"])

        for fields in changes["created"].values():
            filter_obj = create_filter(
                actor=actor, tenant_id=tenant_id, name=fields["name"], description=fields["description"]
            )
            write_filter_tags(actor=actor, tenant_id=tenant_id, filter_obj=filter_obj, tag_ids=fields["tag_ids"])
    except ValidationError as exc:
        raise FilterDraftError(" ".join(exc.messages)) from exc

    draft.delete()
