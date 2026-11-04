from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.draft import Draft
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.services.delete import delete_rule, remove_tag_from_object
from backend.services.draft import (
    DraftError,
    added_entry,
    changes_pending,
    compared_entry,
    discard_draft,
    effective_fields,
    empty_changes,
    get_changes,
    get_draft,
    removed_entry,
    require_editable_row,
    require_rows_still_exist,
    saved_key,
    set_row_fields,
    stage_create,
    stage_delete,
    store_changes,
)
from backend.services.filter_objects.create_filter_objects import create_rule
from backend.services.get import (
    get_all_rules_with_objects_from_filter,
    get_all_tags_from_object,
)
from backend.services.helper_user_tenant import require_write_tenant
from backend.services.membership import (
    add_objects_to_rule,
    add_tag_to_object,
    update_objects_in_rule,
)
from constants import GLOBAL_TENANT_ID

# Pending rule changes are stored in a Draft per (user, filter), under this scope.
RULE_DRAFT_SCOPE = "filter_rules"

ADDRESS_OBJECT_TYPES = {"address", "addressgroup"}
SERVICE_OBJECT_TYPES = {"service", "servicegroup"}

# The selector fields of a rule, with the object types each one accepts and the match type it is stored as.
RULE_OBJECT_FIELDS = {
    "source_address_ids": (ADDRESS_OBJECT_TYPES, "source"),
    "destination_address_ids": (ADDRESS_OBJECT_TYPES, "destination"),
    "source_service_ids": (SERVICE_OBJECT_TYPES, "source"),
    "destination_service_ids": (SERVICE_OBJECT_TYPES, "destination"),
}

RULE_FIELDS = (
    "name",
    "description",
    "action",
    "log_type",
    "enable",
    *RULE_OBJECT_FIELDS,
    "tag_ids",
)


# The same class as DraftError, so `except RuleDraftError` also catches errors raised in backend.services.draft.
RuleDraftError = DraftError


"""
====================================================================
Rule Selector Helpers
====================================================================
"""


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


# The objects behind typed ids such as "address-1", keyed by typed id. Ids whose object doesn't exist are left out.
def objects_by_typed_id(typed_ids, tenant_id: int) -> dict[str, object]:
    _ordered, grouped = parse_typed_ids(",".join(typed_ids))
    return {
        f"{object_type}-{object_id}": obj
        for object_type, objects in fetch_objects_by_type(grouped, tenant_id).items()
        for object_id, obj in objects.items()
    }


"""
====================================================================
Rule Form
====================================================================
"""


# Reads the rule modal form into a fields dict. Selector fields hold typed ids, such as "address-1".
def parse_rule_form(post) -> dict:
    def split_ids(raw_value):
        return [value.strip() for value in (raw_value or "").split(",") if value.strip()]

    try:
        # Sorted, so the same selection always compares equal.
        tag_ids = sorted({int(tag_id) for tag_id in post.getlist("tag_ids") if tag_id})
    except (TypeError, ValueError):
        raise RuleDraftError("Invalid tag selection.")

    return {
        "name": post.get("name", "").strip(),
        "description": post.get("description", "").strip(),
        "action": post.get("action", "").strip(),
        "log_type": post.get("log_type", "").strip(),
        "enable": post.get("enable") == "on",
        **{field: split_ids(post.get(field, "")) for field in RULE_OBJECT_FIELDS},
        "tag_ids": tag_ids,
    }


# Resolves the selector fields to objects, in the order they were selected.
def resolve_rule_objects(fields: dict, tenant_id: int) -> dict[str, list]:
    resolved = {}

    for field, (allowed_types, _match_type) in RULE_OBJECT_FIELDS.items():
        ordered, grouped = parse_typed_ids(",".join(fields[field]))
        validate_rule_selector_types(ordered, allowed_types=allowed_types, field_name=field)
        resolved[field] = build_ordered_object_list(ordered, fetch_objects_by_type(grouped, tenant_id))

    return resolved


# Checks a rule before it goes into the draft, so problems are shown in the modal instead of when saving.
def validate_rule_fields(fields: dict, tenant_id: int) -> None:
    if not all([fields["name"], fields["action"], fields["log_type"]]):
        raise RuleDraftError("Missing required fields.")

    try:
        resolve_rule_objects(fields, tenant_id)
    except ValueError as exc:
        raise RuleDraftError(str(exc))

    found_tags = Tag.objects.filter(id__in=fields["tag_ids"], tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).count()
    if found_tags != len(fields["tag_ids"]):
        raise RuleDraftError("Invalid tag selection.")


"""
====================================================================
Writing Rules
====================================================================
"""


def create_rule_from_fields(*, actor, tenant_id: int, filter_obj: Filter, fields: dict) -> Rule:
    resolved = resolve_rule_objects(fields, tenant_id)

    rule = create_rule(
        actor=actor,
        name=fields["name"],
        description=fields["description"],
        action=fields["action"],
        log_type=fields["log_type"],
        filter=filter_obj,
        tenant_id=tenant_id,
        hit_count=0,
        enable=fields["enable"],
    )

    for field, (_allowed_types, match_type) in RULE_OBJECT_FIELDS.items():
        if resolved[field]:
            add_objects_to_rule(
                actor=actor,
                tenant_id=tenant_id,
                rule_id=rule.id,
                match_type=match_type,
                objects=resolved[field],
            )

    for tag in Tag.objects.filter(id__in=fields["tag_ids"], tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]):
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag, obj=rule)

    return rule


def write_rule_fields(*, actor, tenant_id: int, rule: Rule, fields: dict) -> None:
    resolved = resolve_rule_objects(fields, tenant_id)

    rule.name = fields["name"]
    rule.description = fields["description"]
    rule.action = fields["action"]
    rule.log_type = fields["log_type"]
    rule.enable = fields["enable"]
    rule.save(update_fields=["name", "description", "action", "log_type", "enable"])

    # update_objects_in_rule replaces all matches of a match type, so addresses and services are sent together.
    for match_type in ("source", "destination"):
        update_objects_in_rule(
            actor=actor,
            tenant_id=tenant_id,
            rule_id=rule.id,
            match_type=match_type,
            objects=[
                obj
                for field, (_allowed_types, field_match_type) in RULE_OBJECT_FIELDS.items()
                if field_match_type == match_type
                for obj in resolved[field]
            ],
        )

    current_tags = get_all_tags_from_object(actor=actor, tenant_id=tenant_id, object_id=rule.id, object_type="rule")
    current_tag_ids = {tag.id for tag in current_tags}
    submitted_tag_ids = set(fields["tag_ids"])

    for tag in Tag.objects.filter(
        id__in=submitted_tag_ids - current_tag_ids,
        tenant_id__in=[tenant_id, GLOBAL_TENANT_ID],
    ):
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag, obj=rule)

    for tag_id in current_tag_ids - submitted_tag_ids:
        remove_tag_from_object(
            actor=actor,
            tenant_id=tenant_id,
            object_id=rule.id,
            object_type="rule",
            tag_id=tag_id,
        )


"""
====================================================================
Baseline (the saved rules)
====================================================================
"""


# Rules are identified by row key: "rule-<id>" for saved rules and "ruledraft-<n>" for rules created in the draft.
def saved_rule_key(rule_id: int) -> str:
    return saved_key("rule", rule_id)


# The saved rules of a filter, with their fields in the same format as parse_rule_form, so they can be compared.
def load_baseline_rules(actor, tenant_id: int, filter_id: int) -> list[dict]:
    rules = get_all_rules_with_objects_from_filter(actor, tenant_id, filter_id)

    tag_ids_by_rule = {
        rule.id: sorted(tag_object.tag_id for tag_object in rule.tag_objects.all())
        for rule in Rule.objects.filter(id__in=[rule["rule_id"] for rule in rules]).prefetch_related("tag_objects")
    }

    baseline = []
    for rule in rules:
        fields = {
            "name": rule["rule_name"],
            "description": rule["rule_description"] or "",
            "action": rule["rule_action"] or "",
            "log_type": rule["rule_log_type"] or "",
            "enable": rule["rule_enable"],
            **{field: [] for field in RULE_OBJECT_FIELDS},
            "tag_ids": tag_ids_by_rule.get(rule["rule_id"], []),
        }

        for obj in rule["objects"]:
            object_type = (obj.get("object_type") or "").lower()
            match_type = obj.get("match_type")
            for field, (allowed_types, field_match_type) in RULE_OBJECT_FIELDS.items():
                if object_type in allowed_types and match_type == field_match_type:
                    fields[field].append(f"{object_type}-{obj['object_id']}")

        baseline.append(
            {
                "key": saved_rule_key(rule["rule_id"]),
                "rule_id": rule["rule_id"],
                "tenant_id": rule["rule_tenant_id"],
                "hit_count": rule["rule_hit_count"],
                "date_created": rule["rule_date_created"],
                "date_changed": rule["rule_date_changed"],
                "fields": fields,
            }
        )

    return baseline


"""
====================================================================
Draft Storage
====================================================================
"""


def empty_rule_changes() -> dict:
    # order is the full row order (None when unchanged), and moved lists the rows the user dragged.
    return {**empty_changes(), "order": None, "moved": []}


def get_rule_draft(actor, tenant_id: int, filter_id: int) -> Draft | None:
    return get_draft(actor, tenant_id, RULE_DRAFT_SCOPE, filter_id)


def get_rule_changes(actor, tenant_id: int, filter_id: int) -> dict:
    return {**empty_rule_changes(), **get_changes(actor, tenant_id, RULE_DRAFT_SCOPE, filter_id)}


def rule_changes_pending(changes: dict) -> bool:
    return changes_pending(changes)


def _store_rule_changes(actor, tenant_id: int, filter_id: int, changes: dict) -> None:
    store_changes(actor, tenant_id, RULE_DRAFT_SCOPE, filter_id, changes)


def discard_rule_draft(actor, tenant_id: int, filter_id: int) -> None:
    discard_draft(actor, tenant_id, RULE_DRAFT_SCOPE, filter_id)


"""
====================================================================
Draft State
====================================================================
"""


def _default_order(baseline: list[dict], changes: dict) -> list[str]:
    deleted = set(changes["deleted"])
    return [rule["key"] for rule in baseline if rule["key"] not in deleted] + list(changes["created"])


# The row order with the draft applied. Rows added or removed since the order was stored are
# placed as in the default order, so a stale order never hides or duplicates a rule.
def current_rule_order(baseline: list[dict], changes: dict) -> list[str]:
    default_order = _default_order(baseline, changes)
    if changes["order"] is None:
        return default_order

    visible = set(default_order)
    stored = [key for key in changes["order"] if key in visible]
    stored_keys = set(stored)
    return stored + [key for key in default_order if key not in stored_keys]


def _load_rule_state(actor, tenant_id: int, filter_id: int):
    # A filter that was deleted, or belongs to another tenant, is reported to the user instead of failing.
    try:
        baseline = load_baseline_rules(actor, tenant_id, filter_id)
    except ObjectDoesNotExist:
        raise RuleDraftError("Filter not found.")
    baseline_by_key = {rule["key"]: rule for rule in baseline}
    return baseline, baseline_by_key, get_rule_changes(actor, tenant_id, filter_id)


# Rule names are unique within a filter. The names are checked as the user sees them with the draft applied,
# plus saved rules in the filter the user can't see (other tenants), which the database constraint also counts.
def _require_unique_name(name: str, key: str | None, filter_id: int, baseline: list[dict], changes: dict) -> None:
    error = RuleDraftError("A rule with this name already exists in this filter.")
    baseline_by_key = {rule["key"]: rule for rule in baseline}

    for other_key in current_rule_order(baseline, changes):
        if other_key != key and effective_fields(other_key, baseline_by_key, changes)["name"] == name:
            raise error

    hidden_rules = Rule.objects.filter(filter_id=filter_id).exclude(id__in=[rule["rule_id"] for rule in baseline])
    if hidden_rules.filter(name=name).exists():
        raise error


"""
====================================================================
Staging Changes
====================================================================
"""


def stage_rule_create(*, actor, tenant_id: int, filter_id: int, fields: dict) -> str:
    require_write_tenant(actor, tenant_id)
    baseline, _baseline_by_key, changes = _load_rule_state(actor, tenant_id, filter_id)

    validate_rule_fields(fields, tenant_id)
    _require_unique_name(fields["name"], None, filter_id, baseline, changes)

    key = stage_create(changes, "rule", fields)

    _store_rule_changes(actor, tenant_id, filter_id, changes)
    return key


def stage_rule_update(*, actor, tenant_id: int, filter_id: int, key: str, fields: dict) -> None:
    require_write_tenant(actor, tenant_id)
    baseline, baseline_by_key, changes = _load_rule_state(actor, tenant_id, filter_id)
    require_editable_row(actor, key, baseline_by_key, changes, "rule")

    validate_rule_fields(fields, tenant_id)
    _require_unique_name(fields["name"], key, filter_id, baseline, changes)

    set_row_fields(key, fields, baseline_by_key, changes)
    _store_rule_changes(actor, tenant_id, filter_id, changes)


def stage_rule_enable_toggle(*, actor, tenant_id: int, filter_id: int, key: str) -> None:
    require_write_tenant(actor, tenant_id)
    _baseline, baseline_by_key, changes = _load_rule_state(actor, tenant_id, filter_id)
    require_editable_row(actor, key, baseline_by_key, changes, "rule")

    fields = {**effective_fields(key, baseline_by_key, changes)}
    fields["enable"] = not fields["enable"]

    set_row_fields(key, fields, baseline_by_key, changes)
    _store_rule_changes(actor, tenant_id, filter_id, changes)


def stage_rule_delete(*, actor, tenant_id: int, filter_id: int, key: str) -> None:
    require_write_tenant(actor, tenant_id)
    baseline, baseline_by_key, changes = _load_rule_state(actor, tenant_id, filter_id)
    require_editable_row(actor, key, baseline_by_key, changes, "rule")

    stage_delete(changes, key)

    # Deleting the only moved rule can leave the saved order, so nothing is moved any more.
    if changes["order"] == _default_order(baseline, changes):
        changes["order"] = None
        changes["moved"] = []

    _store_rule_changes(actor, tenant_id, filter_id, changes)


# order is every row key in the order shown after the drop, and moved_key is the row that was dragged.
def stage_rule_order(*, actor, tenant_id: int, filter_id: int, order: list[str], moved_key: str) -> None:
    require_write_tenant(actor, tenant_id)
    baseline, baseline_by_key, changes = _load_rule_state(actor, tenant_id, filter_id)
    require_editable_row(actor, moved_key, baseline_by_key, changes, "rule")

    if sorted(order) != sorted(current_rule_order(baseline, changes)):
        raise RuleDraftError("The rule list has changed. Refresh the page and try again.")

    if order == _default_order(baseline, changes):
        # Dragged back to the saved order, so nothing is moved any more.
        changes["order"] = None
        changes["moved"] = []
    else:
        changes["order"] = order
        if moved_key not in changes["moved"]:
            changes["moved"].append(moved_key)

    _store_rule_changes(actor, tenant_id, filter_id, changes)


"""
====================================================================
Changeset (the differences between the saved rules and the draft)
====================================================================
"""


# Builds one entry per rule, in display order. Removed rules are placed where they were in the saved order.
# Entries only hold plain values, so the changeset can be stored as JSON.
def build_rule_changeset(baseline: list[dict], changes: dict) -> list[dict]:
    baseline_by_key = {rule["key"]: rule for rule in baseline}
    baseline_sequence = {rule["key"]: index for index, rule in enumerate(baseline, start=1)}
    order = current_rule_order(baseline, changes)
    visible = set(order)
    moved = set(changes["moved"])

    # Each removed rule is shown just before the next saved rule that is still there.
    removed_before = {}
    pending_removed = []
    for rule in baseline:
        if rule["key"] in visible:
            if pending_removed:
                removed_before[rule["key"]] = pending_removed
                pending_removed = []
        else:
            pending_removed.append(rule["key"])
    trailing_removed = pending_removed

    def removed_rule_entry(key):
        entry = removed_entry(key, baseline_by_key[key]["fields"])
        return {**entry, "sequence": None, "previous_sequence": baseline_sequence[key], "moved": False}

    changeset = []
    for sequence, key in enumerate(order, start=1):
        changeset.extend(removed_rule_entry(removed_key) for removed_key in removed_before.get(key, []))

        if key in changes["created"]:
            entry = added_entry(key, changes["created"][key])
            changeset.append({**entry, "sequence": sequence, "previous_sequence": None, "moved": False})
            continue

        previous_fields = baseline_by_key[key]["fields"]
        entry = compared_entry(key, changes["updated"].get(key, previous_fields), previous_fields, RULE_FIELDS)
        # A sequence change only counts for the rule that was dragged, not the rules it pushed along.
        was_moved = key in moved and sequence != baseline_sequence[key]
        if was_moved:
            entry["status"] = "changed"

        changeset.append(
            {**entry, "sequence": sequence, "previous_sequence": baseline_sequence[key], "moved": was_moved}
        )

    changeset.extend(removed_rule_entry(removed_key) for removed_key in trailing_removed)
    return changeset


"""
====================================================================
Saving
====================================================================
"""


# The final order of every rule in the filter. Rules the user can't see (other tenants) keep their place:
# each stays right after the visible rule it followed in the saved order, or first if no visible rule came before it.
def _place_hidden_rules(
    saved_ids: list[int], visible_saved_ids: set[int], deleted_ids: set[int], visible_order: list[int]
) -> list[int]:
    hidden_after = {}
    anchor = None
    for rule_id in saved_ids:
        if rule_id not in visible_saved_ids:
            hidden_after.setdefault(anchor, []).append(rule_id)
        elif rule_id not in deleted_ids:
            anchor = rule_id

    ordered_ids = list(hidden_after.get(None, []))
    for rule_id in visible_order:
        ordered_ids.append(rule_id)
        ordered_ids.extend(hidden_after.get(rule_id, []))
    return ordered_ids


# Writes the whole draft in one transaction, so either every change is saved or none are.
@transaction.atomic
def apply_rule_draft(*, actor, tenant_id: int, filter_id: int) -> None:
    require_write_tenant(actor, tenant_id)

    draft = get_rule_draft(actor, tenant_id, filter_id)
    if draft is None:
        return

    filter_obj = Filter.objects.filter(id=filter_id, tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).first()
    if filter_obj is None:
        raise RuleDraftError("The filter no longer exists.")

    baseline, baseline_by_key, changes = _load_rule_state(actor, tenant_id, filter_id)
    # Read before the deletes below, since rules other tenants own are placed relative to the saved order.
    saved_ids = list(
        Rule.objects.filter(filter=filter_obj).order_by("rule_sequence", "id").values_list("id", flat=True)
    )

    require_rows_still_exist(actor, changes, baseline_by_key, "rule")

    for key in changes["deleted"]:
        delete_rule(actor, tenant_id, baseline_by_key[key]["rule_id"])

    for key, fields in changes["updated"].items():
        rule = Rule.objects.get(id=baseline_by_key[key]["rule_id"])
        write_rule_fields(actor=actor, tenant_id=tenant_id, rule=rule, fields=fields)

    created_ids = {}
    for key, fields in changes["created"].items():
        rule = create_rule_from_fields(actor=actor, tenant_id=tenant_id, filter_obj=filter_obj, fields=fields)
        created_ids[key] = rule.id

    if changes["order"] is not None or changes["created"] or changes["deleted"]:
        visible_order = [
            created_ids[key] if key in created_ids else baseline_by_key[key]["rule_id"]
            for key in current_rule_order(baseline, changes)
        ]
        ordered_ids = _place_hidden_rules(
            saved_ids,
            visible_saved_ids={rule["rule_id"] for rule in baseline},
            deleted_ids={baseline_by_key[key]["rule_id"] for key in changes["deleted"]},
            visible_order=visible_order,
        )
        for sequence, rule_id in enumerate(ordered_ids, start=1):
            Rule.objects.filter(id=rule_id).exclude(rule_sequence=sequence).update(rule_sequence=sequence)

    draft.delete()
