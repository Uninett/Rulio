from django.core.exceptions import PermissionDenied

from backend.objects.draft import Draft
from backend.services.helper_user_tenant import can_write_tenant

"""
Unsaved changes a user makes on a page, shared by every page that has Save / Discard.

A page's draft is stored per (user, tenant, scope, scope_id). scope names what is edited (e.g. "filters")
and scope_id which one (e.g. the filter id for "filter_rules"), or 0 when the page isn't tied to one object.

Rows are identified by key: "<type>-<id>" for saved objects (the row ids the tables already use, e.g. "address-1")
and "<type>draft-<n>" for objects only created in the draft (e.g. "addressdraft-1").
"""


class DraftError(ValueError):
    """A draft change that can't be made. The message is shown to the user."""


"""
====================================================================
Row Keys
====================================================================
"""


def saved_key(object_type: str, object_id: int) -> str:
    return f"{object_type}-{object_id}"


# Takes the next free key for an object created in the draft, counting up next_new_id in changes.
def new_key(object_type: str, changes: dict) -> str:
    key = f"{object_type}draft-{changes['next_new_id']}"
    changes["next_new_id"] += 1
    return key


def is_new_key(key: str) -> bool:
    return key.split("-", 1)[0].endswith("draft")


# The object type of a row key, e.g. "address" for both "address-1" and "addressdraft-1".
def key_type(key: str) -> str:
    return key.split("-", 1)[0].removesuffix("draft")


"""
====================================================================
Storage
====================================================================
"""


def empty_changes() -> dict:
    # created/updated map row key -> full fields and deleted lists saved row keys.
    # Pages whose rows can be reordered also store "order", which is None when unchanged.
    return {"created": {}, "updated": {}, "deleted": [], "next_new_id": 1}


def get_draft(actor, tenant_id: int, scope: str, scope_id: int) -> Draft | None:
    return Draft.objects.filter(user=actor, tenant_id=tenant_id, scope=scope, scope_id=scope_id).first()


def get_changes(actor, tenant_id: int, scope: str, scope_id: int) -> dict:
    draft = get_draft(actor, tenant_id, scope, scope_id)
    return {**empty_changes(), **draft.changes} if draft else empty_changes()


def changes_pending(changes: dict) -> bool:
    return bool(changes["created"] or changes["updated"] or changes["deleted"] or changes.get("order") is not None)


# Deletes the draft instead of storing it when nothing is pending, so undoing the last change leaves no draft.
def store_changes(actor, tenant_id: int, scope: str, scope_id: int, changes: dict) -> None:
    if not changes_pending(changes):
        discard_draft(actor, tenant_id, scope, scope_id)
        return

    Draft.objects.update_or_create(
        user=actor,
        tenant_id=tenant_id,
        scope=scope,
        scope_id=scope_id,
        defaults={"changes": changes},
    )


def discard_draft(actor, tenant_id: int, scope: str, scope_id: int) -> None:
    Draft.objects.filter(user=actor, tenant_id=tenant_id, scope=scope, scope_id=scope_id).delete()


"""
====================================================================
Rows
====================================================================
"""

# Baseline rows are dicts with at least "key", "tenant_id" (the row's owner, for write checks)
# and "fields" (the saved values, in the same format as the page's form).


# The fields of a row with the draft applied. baseline_by_key maps row key -> saved row, which holds "fields".
def effective_fields(key: str, baseline_by_key: dict, changes: dict) -> dict:
    if key in changes["created"]:
        return changes["created"][key]
    if key in changes["updated"]:
        return changes["updated"][key]
    return baseline_by_key[key]["fields"]


# label names the row type in messages, e.g. "rule".
def require_editable_row(actor, key: str, baseline_by_key: dict, changes: dict, label: str) -> None:
    if key in changes["created"]:
        return

    row = baseline_by_key.get(key)
    if row is None or key in changes["deleted"]:
        raise DraftError(f"{label.capitalize()} not found. Refresh the page and try again.")

    if not can_write_tenant(actor, row["tenant_id"]):
        raise PermissionDenied(f"You do not have permission to modify this {label}.")


"""
====================================================================
Staging Changes
====================================================================
"""


def stage_create(changes: dict, object_type: str, fields: dict) -> str:
    key = new_key(object_type, changes)
    changes["created"][key] = fields
    if changes.get("order") is not None:
        changes["order"].append(key)
    return key


# Stores the new fields of a row. A saved row edited back to its saved values is dropped from the draft.
def set_row_fields(key: str, fields: dict, baseline_by_key: dict, changes: dict) -> None:
    if key in changes["created"]:
        changes["created"][key] = fields
    elif fields == baseline_by_key[key]["fields"]:
        changes["updated"].pop(key, None)
    else:
        changes["updated"][key] = fields


def stage_delete(changes: dict, key: str) -> None:
    if key in changes["created"]:
        # A row that only exists in the draft is dropped completely.
        changes["created"].pop(key)
    else:
        changes["updated"].pop(key, None)
        changes["deleted"].append(key)

    if changes.get("order") is not None:
        changes["order"] = [order_key for order_key in changes["order"] if order_key != key]
    if "moved" in changes:
        changes["moved"] = [moved_key for moved_key in changes["moved"] if moved_key != key]


"""
====================================================================
Changeset (the differences between the saved rows and the draft)
====================================================================
"""


# Entries only hold plain values, so a changeset can be stored as JSON.
def added_entry(key: str, fields: dict) -> dict:
    return {
        "key": key,
        "status": "added",
        "fields": fields,
        "previous_fields": None,
        "changed_fields": [],
        "enable_changed": False,
    }


def removed_entry(key: str, previous_fields: dict) -> dict:
    return {
        "key": key,
        "status": "removed",
        "fields": previous_fields,
        "previous_fields": previous_fields,
        "changed_fields": [],
        "enable_changed": False,
    }


# When "enable" is one of field_names it is reported separately, as enable_changed, since it is shown as its own
# toggle. Pages without an enable field are unaffected.
def compared_entry(key: str, fields: dict, previous_fields: dict, field_names) -> dict:
    changed_fields = [field for field in field_names if field != "enable" and fields[field] != previous_fields[field]]
    enable_changed = "enable" in field_names and fields["enable"] != previous_fields["enable"]
    return {
        "key": key,
        "status": "changed" if changed_fields or enable_changed else "unchanged",
        "fields": fields,
        "previous_fields": previous_fields,
        "changed_fields": changed_fields,
        "enable_changed": enable_changed,
    }


# For pages without ordering: the saved rows in saved order, then the created rows in the order they were made.
def build_changeset(baseline: list[dict], changes: dict, field_names) -> list[dict]:
    deleted = set(changes["deleted"])
    changeset = []

    for row in baseline:
        key = row["key"]
        if key in deleted:
            changeset.append(removed_entry(key, row["fields"]))
        else:
            fields = changes["updated"].get(key, row["fields"])
            changeset.append(compared_entry(key, fields, row["fields"], field_names))

    changeset.extend(added_entry(key, fields) for key, fields in changes["created"].items())
    return changeset


"""
====================================================================
Saving
====================================================================
"""


# Rows deleted by someone else since the draft was made can't be updated or deleted again.
# The message names the row by its "name" field when it has one, otherwise by its key.
def require_rows_still_exist(actor, changes: dict, baseline_by_key: dict, label: str) -> None:
    for key in [*changes["updated"], *changes["deleted"]]:
        if key not in baseline_by_key:
            name = changes["updated"].get(key, {}).get("name", key)
            raise DraftError(
                f"{label.capitalize()} '{name}' was deleted by someone else. Discard your changes and try again."
            )
        if not can_write_tenant(actor, baseline_by_key[key]["tenant_id"]):
            raise PermissionDenied(f"You do not have permission to modify this {label}.")
