from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import QuerySet
from django.db.models import F

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.interface import Interface

from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.services.helper_user_tenant import is_superadmin, require_read_tenant
from backend.services.serialize import serialize_rule_object
from backend.utils.logger import set_up_logger
from constants import GLOBAL_TENANT_ID

from collections import defaultdict
from django.contrib.contenttypes.models import ContentType


# Setup logger
logger = set_up_logger(__name__)

DJANGO_MODEL_MAPPING = {
    "address": Address,
    "addressgroup": AddressGroup,
    "service": Service,
    "servicegroup": ServiceGroup,
    "device": Device,
    "devicegroup": DeviceGroup,
    "interface": Interface,
    "rule": Rule,
    "tag": Tag,
    "addressgroupmember": AddressGroupMember,
    "servicegroupmember": ServiceGroupMember,
    "filter": Filter,
}


def get_all_rules_with_objects_from_tenant(actor: User, tenant_id: int) -> list[dict]:
    require_read_tenant(actor, tenant_id)
    allowed_tenant_ids = [tenant_id, GLOBAL_TENANT_ID]
    rules = Rule.objects.filter(tenant_id__in=allowed_tenant_ids).prefetch_related("matches")
    result = []
    for rule in rules:
        rule_dict = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "rule_description": rule.description,
            "rule_tenant_id": rule.tenant_id,
            "rule_action": rule.action,
            "rule_log_type": rule.log_type,
            "rule_hit_count": rule.hit_count,
            "rule_date_created": rule.date_created,
            "rule_date_changed": rule.date_changed,
            "rule_created_by": rule.created_by,
            "rule_changed_by": rule.changed_by,
            "rule_enable": rule.enable,
            "objects": [],
        }
        for match in rule.matches.all():
            obj = match.content_object
            if obj:
                rule_dict["objects"].append(
                    {
                        "object_type": obj.__class__.__name__,
                        "object_id": obj.id,
                        "object_name": getattr(obj, "name", None),
                        "match_type": match.match,
                    }
                )

        result.append(rule_dict)

    return result


def get_all_rules_with_objects_from_filter(actor: User, tenant_id: int, filter_id: int) -> list[dict]:
    require_read_tenant(actor, tenant_id)

    try:
        filter_obj = Filter.objects.get(id=filter_id, tenant_id=tenant_id)
    except Filter.DoesNotExist:
        raise ObjectDoesNotExist(f"Filter with ID {filter_id} does not exist in tenant {tenant_id}.")

    rules = list(
        filter_obj.rules.filter(tenant_id=tenant_id)
        .prefetch_related("matches__object_type")
        .order_by("rule_sequence", "id")
    )

    matches_by_type = defaultdict(set)
    all_matches = []

    for rule in rules:
        for match in rule.matches.all():
            matches_by_type[match.object_type_id].add(match.object_id)
            all_matches.append(match)

    object_cache = {}

    for object_type_id, object_ids in matches_by_type.items():
        content_type = ContentType.objects.get_for_id(object_type_id)
        model_class = content_type.model_class()

        if model_class is None:
            continue

        objects = model_class.objects.filter(id__in=object_ids)
        object_cache[object_type_id] = {obj.id: obj for obj in objects}

    result = []

    for rule in rules:
        serialized_objects = []

        for match in rule.matches.all():
            obj = object_cache.get(match.object_type_id, {}).get(match.object_id)

            if obj is not None:
                serialized_objects.append(
                    {
                        "object_type": obj.__class__.__name__,
                        "object_id": obj.id,
                        "object_name": getattr(obj, "name", None),
                        "match_type": match.match,
                    }
                )

        result.append(
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "rule_description": rule.description,
                "rule_tenant_id": rule.tenant_id,
                "rule_filter_id": rule.filter_id,
                "rule_action": rule.action,
                "rule_log_type": rule.log_type,
                "rule_hit_count": rule.hit_count,
                "rule_date_created": rule.date_created,
                "rule_date_changed": rule.date_changed,
                "rule_created_by": rule.created_by,
                "rule_changed_by": rule.changed_by,
                "rule_enable": rule.enable,
                "rule_sequence": rule.rule_sequence,
                "objects": serialized_objects,
            }
        )

    return result


def get_all_objects_from_rule(
    actor: User,
    tenant_id: int,
    rule_id: int,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Return rule objects grouped as:

    1. Source address/address-group objects
    2. Destination address/address-group objects
    3. Source service/service-group objects
    4. Destination service/service-group objects
    """

    require_read_tenant(actor, tenant_id)

    try:
        rule = Rule.objects.get(id=rule_id)
    except Rule.DoesNotExist as exc:
        raise ObjectDoesNotExist(f"Rule with ID {rule_id} does not exist.") from exc

    if rule.tenant_id != tenant_id and not is_superadmin(actor):
        raise PermissionDenied(f"Rule with ID {rule_id} does not belong to tenant {tenant_id}.")

    # select_related prevents an additional query every time
    # match.object_type is accessed.
    rule_matches = list(RuleMatch.objects.filter(rule=rule).select_related("object_type"))

    address_source_objects: list[dict[str, Any]] = []
    address_destination_objects: list[dict[str, Any]] = []
    service_source_objects: list[dict[str, Any]] = []
    service_destination_objects: list[dict[str, Any]] = []

    address_types = {"address", "addressgroup"}
    service_types = {"service", "servicegroup"}

    supported_model_classes = {
        "address": Address,
        "addressgroup": AddressGroup,
        "service": Service,
        "servicegroup": ServiceGroup,
    }

    # Build a collection of required primary keys per Django content-type
    # model name, so each model type can be retrieved in a single query.
    ids_by_type: dict[str, set[int]] = defaultdict(set)

    for rule_match in rule_matches:
        model_name = rule_match.object_type.model

        if model_name not in supported_model_classes:
            raise ValueError(
                "Unsupported RuleMatch content type: "
                f"{rule_match.object_type.app_label}.{model_name}; "
                f"RuleMatch id={rule_match.id}"
            )

        ids_by_type[model_name].add(rule_match.object_id)

    # Example result:
    # {
    #     "address": {1: <Address ...>, 4: <Address ...>},
    #     "servicegroup": {3: <ServiceGroup ...>},
    # }
    objects_by_type: dict[str, dict[int, Any]] = {
        model_name: model_class.objects.in_bulk(ids_by_type[model_name])
        for model_name, model_class in supported_model_classes.items()
    }

    for rule_match in rule_matches:
        model_name = rule_match.object_type.model
        object_map = objects_by_type[model_name]

        obj = object_map.get(rule_match.object_id)

        # A GenericForeignKey does not automatically enforce database-level
        # referential integrity. Skip a match if its referenced object is gone.
        if obj is None:
            continue

        serialized_object = serialize_rule_object(obj, model_name)

        if model_name in address_types:
            if rule_match.match == "source":
                address_source_objects.append(serialized_object)

            elif rule_match.match == "destination":
                address_destination_objects.append(serialized_object)

            else:
                raise ValueError(
                    "Unsupported match direction for address object: "
                    f"match={rule_match.match!r}; "
                    f"content_type={rule_match.object_type.app_label}.{model_name}; "
                    f"RuleMatch id={rule_match.id}"
                )

        elif model_name in service_types:
            if rule_match.match == "source":
                service_source_objects.append(serialized_object)

            elif rule_match.match == "destination":
                service_destination_objects.append(serialized_object)

            else:
                raise ValueError(
                    "Unsupported match direction for service object: "
                    f"match={rule_match.match!r}; "
                    f"content_type={rule_match.object_type.app_label}.{model_name}; "
                    f"RuleMatch id={rule_match.id}"
                )

    return (
        address_source_objects,
        address_destination_objects,
        service_source_objects,
        service_destination_objects,
    )


def get_rule_with_tags_from_tenant(
    *, actor: User, tenant_id: int, rule_id: int, include_global_tenant=True
) -> tuple[Rule, list[Tag]]:
    require_read_tenant(actor, tenant_id)
    try:
        if include_global_tenant:
            rule = Rule.objects.prefetch_related("tag_objects__tag").get(id=rule_id)
        else:
            rule = Rule.objects.prefetch_related("tag_objects__tag").filter(tenant_id=tenant_id).get(id=rule_id)
    except Rule.DoesNotExist:
        raise ObjectDoesNotExist(f"Rule with ID {rule_id} does not exist.")

    if rule.tenant_id != tenant_id and not is_superadmin(actor):
        raise PermissionDenied(f"Rule with ID {rule_id} does not belong to tenant {tenant_id}.")

    tags = [tc.tag for tc in rule.tag_objects.all()]

    return rule, tags


def get_all_rules_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True):
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        rules = Rule.objects.filter(tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).prefetch_related("tag_objects__tag")
    else:
        rules = Rule.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    result = []
    for rule in rules:
        rule_dict = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "rule_description": rule.description,
            "rule_tenant_id": rule.tenant_id,
            "rule_action": rule.action,
            "rule_log_type": rule.log_type,
            "rule_hit_count": rule.hit_count,
            "rule_date_created": rule.date_created,
            "rule_date_changed": rule.date_changed,
            "rule_created_by": rule.created_by,
            "rule_changed_by": rule.changed_by,
            "rule_enable": rule.enable,
            "rule_sequence": rule.rule_sequence,
            "tags": [
                {
                    "tag_id": tc.tag.id,
                    "tag_name": tc.tag.name,
                    "tag_description": tc.tag.description,
                }
                for tc in rule.tag_objects.all()
            ],
        }
        result.append(rule_dict)

    return result, rules


def get_all_tags_from_object(actor: User, tenant_id: int, object_id: int, object_type: str) -> list[Tag]:
    require_read_tenant(actor, tenant_id)
    obj = get_object_by_type_and_id(actor, tenant_id, object_type, object_id)
    return list(obj.get_tags())


def get_all_tags_from_tenant(actor: User, tenant_id: int, include_global=True) -> list[Tag]:
    require_read_tenant(actor, tenant_id)
    if include_global:
        allowed_tenants = [GLOBAL_TENANT_ID, tenant_id]
    else:
        allowed_tenants = [tenant_id]
    return Tag.objects.filter(tenant_id__in=allowed_tenants)


def get_object_by_type_and_id(actor: User, tenant_id: int, object_type: str, object_id: int):
    require_read_tenant(actor, tenant_id)
    object_type = object_type.lower()
    model = DJANGO_MODEL_MAPPING.get(object_type)
    if not model:
        raise ValueError(f"Unsupported object type: {object_type}")

    try:
        obj = model.objects.get(id=object_id)
    except model.DoesNotExist:
        raise ObjectDoesNotExist(f"{model.__name__} with ID {object_id} does not exist.")

    if obj.tenant_id != int(tenant_id) and obj.tenant_id != GLOBAL_TENANT_ID and not is_superadmin(actor):
        raise PermissionDenied(f"Object with ID {object_id} does not belong to tenant {tenant_id}.")

    return obj


def get_all_rules_from_tenant(actor: User, tenant_id: int) -> QuerySet[Rule]:
    require_read_tenant(actor, tenant_id)
    requested_rules = Rule.objects.filter(tenant_id=tenant_id)
    return requested_rules


def get_all_devices_from_tenant(actor: User, tenant_id: int) -> QuerySet[Device]:
    require_read_tenant(actor, tenant_id)
    requested_devices = Device.objects.filter(tenant_id=tenant_id)
    return requested_devices


def get_all_devices_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True):
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        requested_devices = Device.objects.filter(tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).prefetch_related(
            "tag_objects__tag"
        )
    else:
        requested_devices = Device.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    result = []
    for device in requested_devices:
        result.append(
            {
                "device_id": device.id,
                "device_name": device.name,
                "device_platform": device.platform,
                "device_description": device.description,
                "device_tags": [
                    {
                        "tag_id": tc.tag.id,
                        "tag_name": tc.tag.name,
                        "tag_description": tc.tag.description,
                    }
                    for tc in device.tag_objects.all()
                ],
            }
        )

    return result, requested_devices


def get_all_device_groups_and_devices_with_tags_from_tenant(actor: User, tenant_id: int):
    require_read_tenant(actor, tenant_id)

    device_groups = DeviceGroup.objects.filter(tenant_id=tenant_id).prefetch_related(
        "tag_objects__tag",
        "devicegroupmember_set__device",
    )

    devices = Device.objects.filter(tenant_id=tenant_id).prefetch_related(
        "tag_objects__tag",
    )

    return device_groups, devices


def get_device_group_members(actor: User, tenant_id: int, device_group_id: int) -> QuerySet[Device]:
    require_read_tenant(actor, tenant_id)
    if not DeviceGroup.objects.filter(id=device_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Device group with ID {device_group_id} does not exist in tenant {tenant_id}.")
    return Device.objects.filter(tenant_id=tenant_id, devicegroupmember__device_group_id=device_group_id)


def get_all_interfaces_from_device(actor: User, tenant_id: int, device_id: int) -> QuerySet[Interface]:
    require_read_tenant(actor, tenant_id)
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise ObjectDoesNotExist(f"Device with ID {device_id} does not exist.")

    if not is_superadmin(actor) and device.tenant_id != tenant_id:
        raise PermissionDenied(f"Device with ID {device_id} does not belong to tenant {tenant_id}.")

    return Interface.objects.filter(device=device)


def get_all_filters_from_interface(
    actor: User, tenant_id: int, interface_id: int, direction: str = "any"
) -> QuerySet[Filter]:
    require_read_tenant(actor, tenant_id)
    if direction not in ["in", "out", "any"]:
        raise ValueError(f"Invalid direction: {direction}. Must be 'in', 'out', or 'any'.")

    interface = Interface.objects.filter(id=interface_id).first()
    if interface is None:
        raise ObjectDoesNotExist(f"Interface with ID {interface_id} does not exist.")

    if not is_superadmin(actor) and interface.device.tenant_id != tenant_id:
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")
    if direction == "any":
        requested_filters = Filter.objects.filter(filterinterface__interface_id=interface_id)
    elif direction == "in":
        interface_direction = InterfaceDirection.objects.filter(interface_id=interface_id, direction="in").first()
        if interface_direction is None:
            raise ObjectDoesNotExist(f"No 'in' direction found for interface with ID {interface_id}.")
        requested_filters = Filter.objects.filter(filterinterface__interface_direction=interface_direction)
    elif direction == "out":
        interface_direction = InterfaceDirection.objects.filter(interface_id=interface_id, direction="out").first()
        if interface_direction is None:
            raise ObjectDoesNotExist(f"No 'out' direction found for interface with ID {interface_id}.")
        requested_filters = Filter.objects.filter(filterinterface__interface_direction=interface_direction)

    requested_filters = requested_filters.annotate(
        policy_sequence=F("filterinterface__policy_sequence"),
        interface_enable=F("filterinterface__enable"),
        interface_direction=F("filterinterface__interface_direction__direction"),
    ).order_by("interface_direction", "policy_sequence")

    return requested_filters


def get_all_filters_from_tenant(actor: User, tenant_id: int) -> QuerySet[Filter]:
    require_read_tenant(actor, tenant_id)
    requested_filters = Filter.objects.filter(tenant_id=tenant_id)
    return requested_filters


def get_all_filters_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True):
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        requested_filters = Filter.objects.filter(tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).prefetch_related(
            "tag_objects__tag"
        )
    else:
        requested_filters = Filter.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    result = []
    for filter in requested_filters:
        result.append(
            {
                "filter_id": filter.id,
                "filter_name": filter.name,
                "filter_description": filter.description,
                "filter_enable": filter.enable,
                "filter_tenant_id": filter.tenant_id,
                "filter_tags": [
                    {
                        "tag_id": tc.tag.id,
                        "tag_name": tc.tag.name,
                        "tag_description": tc.tag.description,
                    }
                    for tc in filter.tag_objects.all()
                ],
            }
        )

    return result, requested_filters


def get_filters_with_rules_with_tags_from_tenant(
    actor: User,
    tenant_id: int,
    include_global_tenant: bool = True,
) -> tuple[list[dict], QuerySet[Filter], QuerySet[Rule], QuerySet[Tag]]:
    require_read_tenant(actor, tenant_id)

    if include_global_tenant:
        filters = Filter.objects.filter(tenant_id__in=[tenant_id, 1])
        rules = Rule.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("matches")
    else:
        filters = Filter.objects.filter(tenant_id=tenant_id)
        rules = Rule.objects.filter(tenant_id=tenant_id).prefetch_related("matches")

    result = []
    group_map = {}
    tag_ids = set()

    for filter_obj in filters:
        filter_tags = list(filter_obj.get_tags())
        tag_ids.update(tag.id for tag in filter_tags)

        filter_dict = {
            "filter_id": filter_obj.id,
            "filter_name": filter_obj.name,
            "filter_description": filter_obj.description,
            "filter_enable": filter_obj.enable,
            "filter_tenant_id": filter_obj.tenant_id,
            "tags": [
                {
                    "tag_id": tag.id,
                    "tag_name": tag.name,
                    "tag_tenant_id": tag.tenant_id,
                }
                for tag in filter_tags
            ],
            "rules": [],
        }
        result.append(filter_dict)
        group_map[filter_obj.id] = filter_dict

    for rule in rules:
        if rule.filter_id not in group_map:
            continue

        rule_tags = list(rule.get_tags())
        tag_ids.update(tag.id for tag in rule_tags)

        group_map[rule.filter_id]["rules"].append(
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "rule_description": rule.description,
                "rule_action": rule.action,
                "rule_log_type": rule.log_type,
                "rule_hit_count": rule.hit_count,
                "rule_date_created": rule.date_created,
                "rule_date_changed": rule.date_changed,
                "rule_created_by": rule.created_by,
                "rule_changed_by": rule.changed_by,
                "rule_enable": rule.enable,
                "rule_tenant_id": rule.tenant_id,
                "tags": [
                    {
                        "tag_id": tag.id,
                        "tag_name": tag.name,
                        "tag_tenant_id": tag.tenant_id,
                    }
                    for tag in rule_tags
                ],
            }
        )

    tags = Tag.objects.filter(id__in=tag_ids)

    return result, filters, rules, tags

def get_filter_with_rules_and_tags(
    actor: User,
    tenant_id: int,
    filter_id: int,
) -> dict[str, Any]:
    """
    Retrieve one filter, its rules, and its tags.

    Access is allowed when the filter belongs to the selected tenant,
    belongs to the global tenant, or the actor is a superadmin.
    """

    require_read_tenant(actor, tenant_id)

    try:
        filter_obj = Filter.objects.get(id=filter_id)
    except Filter.DoesNotExist as exc:
        raise ObjectDoesNotExist(
            f"Filter with ID {filter_id} does not exist."
        ) from exc

    allowed_tenant_ids = {tenant_id, GLOBAL_TENANT_ID}

    if (
        filter_obj.tenant_id not in allowed_tenant_ids
        and not is_superadmin(actor)
    ):
        raise PermissionDenied(
            f"Filter with ID {filter_id} does not belong to tenant {tenant_id}."
        )

    rules = (
        Rule.objects
        .filter(filter_id=filter_obj.id)
        .prefetch_related("matches")
    )

    filter_tags = list(filter_obj.get_tags())
    tag_ids = {tag.id for tag in filter_tags}

    serialized_rules: list[dict[str, Any]] = []

    for rule in rules:
        rule_tags = list(rule.get_tags())
        tag_ids.update(tag.id for tag in rule_tags)

        serialized_rules.append(
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "rule_description": rule.description,
                "rule_action": rule.action,
                "rule_log_type": rule.log_type,
                "rule_hit_count": rule.hit_count,
                "rule_date_created": rule.date_created,
                "rule_date_changed": rule.date_changed,
                "rule_created_by": rule.created_by,
                "rule_changed_by": rule.changed_by,
                "rule_enable": rule.enable,
                "rule_tenant_id": rule.tenant_id,
                "tags": [
                    {
                        "tag_id": tag.id,
                        "tag_name": tag.name,
                        "tag_tenant_id": tag.tenant_id,
                    }
                    for tag in rule_tags
                ],
            }
        )

    return {
        "filter_id": filter_obj.id,
        "filter_name": filter_obj.name,
        "filter_description": filter_obj.description,
        "filter_enable": filter_obj.enable,
        "filter_tenant_id": filter_obj.tenant_id,
        "rules": serialized_rules,
        "tags": [
            {
                "tag_id": tag.id,
                "tag_name": tag.name,
                "tag_tenant_id": tag.tenant_id,
            }
            for tag in filter_tags
        ],
        "all_tags": Tag.objects.filter(id__in=tag_ids),
    }

def get_platform_from_device(actor: User, tenant_id: int, device_id: int) -> str:
    require_read_tenant(actor, tenant_id)

    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise ObjectDoesNotExist(f"Device with ID {device_id} does not exist.")

    if not is_superadmin(actor) and device.tenant_id != tenant_id:
        raise PermissionDenied(f"Device with ID {device_id} does not belong to tenant {tenant_id}.")

    return device.platform


def get_all_objects_with_certain_tag(
    actor: User, tenant_id: int, tag_id: int, include_global_tenant=True
) -> tuple[list[dict], dict[str, list]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        tag = Tag.objects.filter(id=tag_id, tenant_id__in=[tenant_id, GLOBAL_TENANT_ID]).first()
    else:
        tag = Tag.objects.filter(id=tag_id, tenant_id=tenant_id).first()

    if tag is None:
        raise ObjectDoesNotExist(f"Tag with ID {tag_id} does not exist or is not accessible to tenant {tenant_id}.")

    if tag.tenant_id != tenant_id and tag.tenant_id != 1 and not is_superadmin(actor):
        raise PermissionDenied(f"Tag with ID {tag_id} does not belong to tenant {tenant_id}.")
    tagged_objects = TagConnection.objects.filter(tag_id=tag_id).select_related("content_type", "tag")

    result = []
    objects = {
        "address": [],
        "addressgroup": [],
        "service": [],
        "servicegroup": [],
        "rule": [],
        "filter": [],
        "device": [],
        "devicegroup": [],
        "interface": [],
    }
    for tagged_object in tagged_objects:
        obj = tagged_object.content_object
        if (
            obj
            and hasattr(obj, "tenant_id")
            and (obj.tenant_id == tenant_id or (include_global_tenant and obj.tenant_id == 1))
            or obj.__class__.__name__.lower() == "interface"
            and obj.device.tenant_id == (tenant_id or (include_global_tenant and obj.device.tenant_id == 1))
        ):
            result.append(
                {
                    "object_type": obj.__class__.__name__,
                    "object_id": obj.id,
                    "object_name": getattr(obj, "name", None),
                }
            )
            if obj.__class__.__name__.lower() in objects:
                objects[obj.__class__.__name__.lower()].append(obj)
            else:
                logger.error(f"Unexpected object type: {obj.__class__.__name__} for object ID {obj.id}")
    return result, objects
