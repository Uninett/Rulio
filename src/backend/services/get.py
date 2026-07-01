from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

from backend.objects import models
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.interface import Interface

from backend.services.helper_user_tenant import require_read_tenant
from backend.utils.logger import set_up_logger


# Setup logger
logger = set_up_logger(__name__)

DJANGO_MODEL_MAPPING = {
    "address": Address,
    "addressgroup": AddressGroup,
    "service": Service,
    "servicegroup": ServiceGroup,
    "rule": Rule,
    "tag": Tag,
    "addressgroupmember": AddressGroupMember,
    "servicegroupmember": ServiceGroupMember,
    "filter": Filter,
}


def get_all_rules_with_objects_from_tenant(actor: User, tenant_id: int) -> list[dict]:
    require_read_tenant(actor, tenant_id)
    rules = Rule.objects.filter(tenant_id=tenant_id).prefetch_related("matches")
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


def get_all_rules_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True):
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        rules = Rule.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
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
    obj = get_object_by_type_and_id(actor, tenant_id, object_id, object_type)
    return list(obj.get_tags())


def get_all_tags_from_tenant(actor: User, tenant_id: int) -> list[Tag]:
    require_read_tenant(actor, tenant_id)
    return Tag.objects.filter(tenant_id=tenant_id)


def get_object_by_type_and_id(actor: User, tenant_id: int, object_type: str, object_id: int):
    require_read_tenant(actor, tenant_id)
    object_type = object_type.lower()
    model = DJANGO_MODEL_MAPPING.get(object_type)
    if not model:
        raise ValueError(f"Unsupported object type: {object_type}")
    obj = model.objects.get(id=object_id)
    if obj.tenant_id != tenant_id:
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
        requested_devices = Device.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
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


def get_all_interfaces_from_device(actor: User, tenant_id: int, device_id: int) -> list[Interface]:
    require_read_tenant(actor, tenant_id)
    if not Device.objects.filter(id=device_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Device with ID {device_id} does not belong to tenant {tenant_id}.")
    requested_interfaces = Interface.objects.filter(device_id=device_id)
    return requested_interfaces


def get_all_filters_from_interface(actor: User, tenant_id: int, interface_id: int) -> QuerySet[Filter]:
    require_read_tenant(actor, tenant_id)
    if not Interface.objects.filter(id=interface_id, device__tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")
    requested_filters = Filter.objects.filter(interfaces__id=interface_id)
    requested_filters = requested_filters.annotate(
        policy_sequence=models.F("filterinterface__policy_sequence"),
        enable=models.F("filterinterface__enable"),
    ).order_by("policy_sequence")
    return requested_filters


def get_all_filters_from_tenant(actor: User, tenant_id: int) -> QuerySet[Filter]:
    require_read_tenant(actor, tenant_id)
    requested_filters = Filter.objects.filter(tenant_id=tenant_id)
    return requested_filters


def get_all_filters_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True):
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        requested_filters = Filter.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
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
                "filter_policy_sequence": filter.policy_sequence,
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


def get_platform_from_device(actor: User, tenant_id: int, device_id: int) -> str:
    require_read_tenant(actor, tenant_id)
    if not Device.objects.filter(id=device_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Device with ID {device_id} does not belong to tenant {tenant_id}.")
    device = Device.objects.get(id=device_id)
    return device.platform


def get_all_objects_with_certain_tag(
    actor: User, tenant_id: int, tag_id: int, include_global_tenant=True
) -> tuple[list[dict], dict[str, list]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        tag = Tag.objects.filter(id=tag_id, tenant_id__in=[tenant_id, 1]).first()
    else:
        tag = Tag.objects.filter(id=tag_id, tenant_id=tenant_id).first()

    if tag.tenant_id != tenant_id and tag.tenant_id != 1:
        raise PermissionDenied(f"Tag with ID {tag_id} does not belong to tenant {tenant_id}.")
    tagged_objects = tag.tagged_objects.all()
    result = []
    objects = {
        "address": [],
        "addressgroup": [],
        "service": [],
        "servicegroup": [],
        "rule": [],
        "filter": [],
        "device": [],
        "interface": [],
    }
    for tagged_object in tagged_objects:
        obj = tagged_object.content_object
        if (
            obj
            and hasattr(obj, "tenant_id")
            and (obj.tenant_id == tenant_id or (include_global_tenant and obj.tenant_id == 1))
        ):
            result.append(
                {
                    "object_type": obj.__class__.__name__,
                    "object_id": obj.id,
                    "object_name": getattr(obj, "name", None),
                }
            )
            objects[obj.__class__.__name__.lower()].append(obj)
    return result, objects
