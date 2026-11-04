from backend.objects.draft import Draft

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
