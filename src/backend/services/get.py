from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

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


def get_all_service_groups_from_tenant(actor: User, tenant_id: int) -> list[ServiceGroup]:
    require_read_tenant(actor, tenant_id)
    requested_service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)
    return requested_service_groups


def get_service_groups_with_services_from_tenant(actor: User, tenant_id: int, get="all") -> list[dict]:
    require_read_tenant(actor, tenant_id)
    service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)
    if get == "objects":
        service_groups_with_services = []
        for service_group in service_groups:
            if service_group.services.exists():
                service_groups_with_services.append(service_group)
        return service_groups_with_services
    result = []
    group_map = {}

    for group in service_groups:
        group_dict = {
            "service_group_id": group.id,
            "service_group_name": group.name,
            "services": [],
        }
        result.append(group_dict)
        group_map[group.id] = group_dict

    memberships = ServiceGroupMember.objects.filter(
        group__tenant_id=tenant_id,
        service__tenant_id=tenant_id,
    ).select_related("group", "service")

    for membership in memberships:
        group_id = membership.group.id

        if group_id in group_map:
            group_map[group_id]["services"].append(
                {
                    "service_id": membership.service.id,
                    "service_name": membership.service.name,
                    "description": membership.service.description,
                    "protocol": membership.service.protocol,
                    "port_start": membership.service.port_start,
                    "port_end": membership.service.port_end,
                }
            )
    if get == "all":
        return result
    elif get == "ids":
        return [{"service_group_id": group["service_group_id"]} for group in result]
    elif get == "names":
        return [{"service_group_name": group["service_group_name"]} for group in result]


def get_address_groups_with_addresses_from_tenant(actor: User, tenant_id: int, get="all") -> list[dict]:
    require_read_tenant(actor, tenant_id)
    address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)

    result = []
    group_map = {}

    for group in address_groups:
        group_dict = {
            "address_group_id": group.id,
            "address_group_name": group.name,
            "addresses": [],
        }
        result.append(group_dict)
        group_map[group.id] = group_dict

    memberships = AddressGroupMember.objects.filter(
        group__tenant_id=tenant_id,
        address__tenant_id=tenant_id,
    ).select_related("group", "address")

    for membership in memberships:
        group_id = membership.group.id

        if group_id in group_map:
            group_map[group_id]["addresses"].append(
                {
                    "address_id": membership.address.id,
                    "address_name": membership.address.name,
                    "addr_type": membership.address.addr_type,
                    "ipv4_type": membership.address.ipv4_type,
                    "ipv6_type": membership.address.ipv6_type,
                    "ipv4Network": membership.address.ipv4Network,
                    "ipv6Network": membership.address.ipv6Network,
                    "ipv4Address_start": membership.address.ipv4Address_start,
                    "ipv4Address_end": membership.address.ipv4Address_end,
                    "ipv6Address_start": membership.address.ipv6Address_start,
                    "ipv6Address_end": membership.address.ipv6Address_end,
                }
            )

    if get == "all":
        return result
    elif get == "ids":
        return [{"address_group_id": group["address_group_id"]} for group in result]
    elif get == "names":
        return [{"address_group_name": group["address_group_name"]} for group in result]

def get_all_addresss_groups_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True) -> list[dict]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        address_groups = AddressGroup.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
    else:
        address_groups = AddressGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    result = []
    for group in address_groups:
        result.append(
            {
                "address_group_id": group.id,
                "address_group_name": group.name,
                "address_group_description": group.description,
                "address_group_tags": [
                    {
                        "tag_id": tc.tag.id,
                        "tag_name": tc.tag.name,
                        "tag_description": tc.tag.description,
                    }
                    for tc in group.tag_objects.all()
                ],
            }
        )

    return result, address_groups

def get_all_addresses_and_groups_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True) -> list[dict]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        address_groups = AddressGroup.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
        addresses = Address.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
    else:
        address_groups = AddressGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")
        addresses = Address.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    memberships = AddressGroupMember.objects.filter(
        group__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
        address__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
    ).select_related("group", "address")

    addresses_by_group = {}
    groups_by_address = {}

    for membership in memberships:
        group = membership.group
        address = membership.address

        addresses_by_group.setdefault(group.id, []).append(
            {
                "id": address.id,
                "name": address.name,
            }
        )

        groups_by_address.setdefault(address.id, []).append(
            {
                "id": group.id,
                "name": group.name,
            }
        )

    result = []

    for group in address_groups:
        result.append(
            {
                "type": "AddressGroup",
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in group.tag_objects.all()
                ],
                "addresses": addresses_by_group.get(group.id, []),
            }
        )

    for address in addresses:
        result.append(
            {
                "type": "Address",
                "id": address.id,
                "name": address.name,
                "description": address.description,
                "addr_type": address.addr_type,
                "ipv4_type": address.ipv4_type,
                "ipv6_type": address.ipv6_type,
                "ipv4Network": address.ipv4Network,
                "ipv6Network": address.ipv6Network,
                "ipv4Address_start": address.ipv4Address_start,
                "ipv4Address_end": address.ipv4Address_end,
                "ipv6Address_start": address.ipv6Address_start,
                "ipv6Address_end": address.ipv6Address_end,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in address.tag_objects.all()
                ],
                "address_groups": groups_by_address.get(address.id, []),
            }
        )

    return result, addresses, address_groups


def get_all_services_and_groups_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True):
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        service_groups = ServiceGroup.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
        services = Service.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
    else:
        service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")
        services = Service.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    memberships = ServiceGroupMember.objects.filter(
        group__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
        service__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
    ).select_related("group", "service")

    services_by_group = {}
    groups_by_service = {}

    for membership in memberships:
        group = membership.group
        service = membership.service

        services_by_group.setdefault(group.id, []).append(
            {
                "id": service.id,
                "name": service.name,
            }
        )

        groups_by_service.setdefault(service.id, []).append(
            {
                "id": group.id,
                "name": group.name,
            }
        )

    result = []

    for group in service_groups:
        result.append(
            {
                "type": "ServiceGroup",
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in group.tag_objects.all()
                ],
                "services": services_by_group.get(group.id, []),
            }
        )

    for service in services:
        result.append(
            {
                "type": "Service",
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "protocol": service.protocol,
                "port_start": service.port_start,
                "port_end": service.port_end,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in service.tag_objects.all()
                ],
                "service_groups": groups_by_service.get(service.id, []),
            }
        )

    return result, services, service_groups


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


def get_all_address_groups_from_tenant(actor: User, tenant_id: int) -> list[AddressGroup]:
    require_read_tenant(actor, tenant_id)
    requested_address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)
    return requested_address_groups


def get_all_addresses_from_tenant(actor: User, tenant_id: int, get="all") -> list:
    require_read_tenant(actor, tenant_id)
    requested_addresses = Address.objects.filter(tenant_id=tenant_id)
    if get == "all":
        return requested_addresses
    elif get == "ids":
        return [{"address_id": address.id} for address in requested_addresses]
    elif get == "names":
        return [{"address_name": address.name} for address in requested_addresses]


def get_all_addresses_from_tenant_by_names(actor: User, tenant_id: int, names: list[str]) -> list[Address]:
    require_read_tenant(actor, tenant_id)
    requested_addresses = Address.objects.filter(tenant_id=tenant_id, name__in=names)
    return requested_addresses


def get_address_group_members(actor: User, tenant_id: int, address_group_id: int) -> list[Address]:
    require_read_tenant(actor, tenant_id)
    if not AddressGroup.objects.filter(id=address_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")
    return Address.objects.filter(addressgroupmember__group_id=address_group_id)
    # return AddressGroupMember.objects.filter(group_id=address_group_id)


def get_all_services_from_tenant(actor: User, tenant_id: int, get="all") -> list[Service]:
    require_read_tenant(actor, tenant_id)
    requested_services = Service.objects.filter(tenant_id=tenant_id)
    if get == "all":
        return requested_services
    elif get == "ids":
        return [{"service_id": service.id} for service in requested_services]
    elif get == "names":
        return [{"service_name": service.name} for service in requested_services]


def get_all_services_from_tenant_by_names(actor: User, tenant_id: int, names: list[str]) -> list[Service]:
    require_read_tenant(actor, tenant_id)
    requested_services = Service.objects.filter(tenant_id=tenant_id, name__in=names)
    return requested_services


def get_service_group_members(actor: User, tenant_id: int, service_group_id: int) -> list[Address]:
    require_read_tenant(actor, tenant_id)
    if not ServiceGroup.objects.filter(id=service_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")
    return Service.objects.filter(servicegroupmember__group_id=service_group_id)
    # return ServiceGroupMember.objects.filter(group_id=service_group_id)


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


def get_all_rules_from_tenant(actor: User, tenant_id: int) -> list[Rule]:
    require_read_tenant(actor, tenant_id)
    requested_rules = Rule.objects.filter(tenant_id=tenant_id)
    return requested_rules


def get_all_devices_from_tenant(actor: User, tenant_id: int) -> list[Device]:
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


def get_all_filters_from_interface(actor: User, tenant_id: int, interface_id: int) -> list[Filter]:
    require_read_tenant(actor, tenant_id)
    if not Interface.objects.filter(id=interface_id, device__tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")
    requested_filters = Filter.objects.filter(interfaces__id=interface_id)
    requested_filters = requested_filters.annotate(
        policy_sequence=models.F("filterinterface__policy_sequence"),
        enable=models.F("filterinterface__enable"),
    ).order_by("policy_sequence")
    return requested_filters


def get_all_filters_from_tenant(actor: User, tenant_id: int) -> list[Filter]:
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

def get_all_objects_with_certain_tag(actor: User, tenant_id: int, tag_id: int, include_global_tenant=True) -> list[dict]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        tag = Tag.objects.filter(id=tag_id, tenant_id__in=[tenant_id, 1]).first()
    else:
        tag = Tag.objects.filter(id=tag_id, tenant_id=tenant_id).first()

    if tag.tenant_id != tenant_id and tag.tenant_id != 1:
        raise PermissionDenied(f"Tag with ID {tag_id} does not belong to tenant {tenant_id}.")
    tagged_objects = tag.tagged_objects.all()
    result = []
    for tagged_object in tagged_objects:
        obj = tagged_object.content_object
        if obj and hasattr(obj, "tenant_id") and (obj.tenant_id == tenant_id or (include_global_tenant and obj.tenant_id == 1)):
            result.append(
                {
                    "object_type": obj.__class__.__name__,
                    "object_id": obj.id,
                    "object_name": getattr(obj, "name", None),
                }
            )
    return result

