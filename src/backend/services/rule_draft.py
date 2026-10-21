from django.core.exceptions import PermissionDenied
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
from backend.services.filter_objects.create_filter_objects import create_rule
from backend.services.get import get_all_rules_with_objects_from_filter, get_all_tags_from_object
from backend.services.helper_user_tenant import can_write_tenant, require_write_tenant
from backend.services.membership import add_objects_to_rule, add_tag_to_object, update_objects_in_rule
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


class RuleDraftError(ValueError):
    """A draft change that can't be made. The message is shown to the user."""


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
