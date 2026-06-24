from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from django.core.exceptions import ValidationError as DjangoValidationError

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule_filter import RuleFilter
from backend.objects.management.device_group_member import DeviceGroupMember
from backend.objects.management.tenant import Tenant
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.objects.attributes.tag import Tag
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.filters.rule import Rule
from backend.services.generate_config import Policy, PolicyRule, generate_config
from backend.objects.management.device import Device
from backend.objects.management.device_group import DeviceGroup
from backend.utils.logger import set_up_logger
from backend.services.get import get_object_by_type_and_id
from django.db import transaction
from backend.services.membership import (
    add_addresses_to_group,
    add_services_to_group,
)
from backend.services.get import get_current_tenant, get_current_tenant_id


# Setup logger
logger = set_up_logger(__name__)


""""
====================================================================
ATTRIBUTES
====================================================================
"""


def create_address(
    request: object,
    name: str,
    description: str,
    addr_type: str | None = "host",
    ipv4_type: str | None = None,
    ipv6_type: str | None = None,
    ipv4Network: IPv4Network | None = None,
    ipv6Network: IPv6Network | None = None,
    ipv4Address_start: IPv4Address | None = None,
    ipv4Address_end: IPv4Address | None = None,
    ipv6Address_start: IPv6Address | None = None,
    ipv6Address_end: IPv6Address | None = None,
) -> Address:
    tenant_id = get_current_tenant_id(request)

    address = Address(
        name=name,
        description=description,
        tenant_id=tenant_id,
        addr_type=addr_type,
        ipv4_type=ipv4_type,
        ipv6_type=ipv6_type,
        ipv4Network=str(ipv4Network) if ipv4Network else None,
        ipv6Network=str(ipv6Network) if ipv6Network else None,
        ipv4Address_start=str(ipv4Address_start) if ipv4Address_start else None,
        ipv4Address_end=str(ipv4Address_end) if ipv4Address_end else None,
        ipv6Address_start=str(ipv6Address_start) if ipv6Address_start else None,
        ipv6Address_end=str(ipv6Address_end) if ipv6Address_end else None,
    )

    try:
        address.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Address validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    address.save()
    logger.info(f"Created {address} for tenant={address.tenant_id}")
    return address


def get_or_create_address(
    request: object,
    name: str,
    description: str,
    addr_type: str | None = "host",
    ipv4_type: str | None = None,
    ipv6_type: str | None = None,
    ipv4Network: IPv4Network | None = None,
    ipv6Network: IPv6Network | None = None,
    ipv4Address_start: IPv4Address | None = None,
    ipv4Address_end: IPv4Address | None = None,
    ipv6Address_start: IPv6Address | None = None,
    ipv6Address_end: IPv6Address | None = None,
) -> tuple[Address, int, bool]:
    tenant_id = get_current_tenant_id(request)

    address, created = Address.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
        addr_type=addr_type,
        ipv4_type=ipv4_type,
        ipv6_type=ipv6_type,
        ipv4Network=str(ipv4Network) if ipv4Network else None,
        ipv6Network=str(ipv6Network) if ipv6Network else None,
        ipv4Address_start=str(ipv4Address_start) if ipv4Address_start else None,
        ipv4Address_end=str(ipv4Address_end) if ipv4Address_end else None,
        ipv6Address_start=str(ipv6Address_start) if ipv6Address_start else None,
        ipv6Address_end=str(ipv6Address_end) if ipv6Address_end else None,
    )
    if created:
        logger.info(f"Created {address} for tenant={address.tenant_id}")
    else:
        logger.warning(f"Address already exists: {address} for tenant={address.tenant_id}")
    return address, address.id, created


def create_service(
    request: object,
    name: str,
    description: str,
    protocol: str,
    port_start: int | None = None,
    port_end: int | None = None,
) -> Service:

    tenant_id = get_current_tenant_id(request)

    service = Service(
        name=name,
        description=description,
        tenant_id=tenant_id,
        protocol=protocol,
        port_start=port_start,
        port_end=port_end,
    )
    try:
        service.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Service validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    service.save()
    logger.info(f"Created {service} for tenant={service.tenant_id}")
    return service


def get_or_create_service(
    request: object,
    name: str,
    description: str,
    protocol: str,
    port_start: int | None = None,
    port_end: int | None = None,
) -> tuple[Service, int, bool]:

    tenant_id = get_current_tenant_id(request)

    service, created = Service.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
        protocol=protocol,
        port_start=port_start,
        port_end=port_end,
    )
    if created:
        logger.info(f"Created {service} for tenant={service.tenant_id}")
    else:
        logger.warning(f"Service already exists: {service} for tenant={service.tenant_id}")
    return service, service.id, created


def create_service_group(
    request: object,
    name: str,
    description: str,
) -> ServiceGroup:

    tenant_id = get_current_tenant_id(request)

    service_group = ServiceGroup(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    try:
        service_group.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Service Group validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    service_group.save()
    logger.info(f"Created {service_group} for tenant={service_group.tenant_id}")
    return service_group


def get_or_create_service_group(
    request: object,
    name: str,
    description: str,
    members: list[int] | None = None,
) -> tuple[ServiceGroup, int, bool]:

    tenant_id = get_current_tenant_id(request)

    service_group, created = ServiceGroup.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    if created:
        logger.info(f"Created {service_group} for tenant={service_group.tenant_id}")
        if members:
            add_services_to_group(service_group_id=service_group.id, service_ids=members)
            logger.info(f"Added members to {service_group}: {members}")
    else:
        logger.warning(f"Service Group already exists: {service_group} for tenant={service_group.tenant_id}")
        if members:
            add_services_to_group(service_group_id=service_group.id, service_ids=members)
            logger.info(f"Added members to existing {service_group}: {members}")
    return service_group, service_group.id, created


def create_address_group(
    request: object,
    name: str,
    description: str,
) -> AddressGroup:

    tenant_id = get_current_tenant_id(request)

    address_group = AddressGroup(
        name=name,
        description=description,
        tenant_id=tenant_id,
        addr_type="Group",
    )
    try:
        address_group.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Address Group validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    address_group.save()
    logger.info(f"Created {address_group} for tenant={address_group.tenant_id}")
    return address_group


def get_or_create_address_group(
    request: object,
    name: str,
    description: str,
    members: list[int] | None = None,
) -> tuple[AddressGroup, int, bool]:

    tenant_id = get_current_tenant_id(request)

    address_group, created = AddressGroup.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
        addr_type="Group",
    )
    if created:
        logger.info(f"Created {address_group} for tenant={address_group.tenant_id}")
        if members:
            add_addresses_to_group(address_group_id=address_group.id, address_ids=members)
            logger.info(f"Added members to {address_group}: {members}")
    else:
        logger.warning(f"Address Group already exists: {address_group} for tenant={address_group.tenant_id}")
        if members:
            add_addresses_to_group(address_group_id=address_group.id, address_ids=members)
            logger.info(f"Added members to existing {address_group}: {members}")

    return address_group, address_group.id, created


def create_tag(request: object, name: str, description: str) -> Tag:
    tenant_id = get_current_tenant_id(request)

    tag = Tag(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    try:
        tag.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Tag validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    tag.save()
    logger.info(f"Created {tag} for tenant={tag.tenant_id}")
    return tag


def create_and_add_tag_to_object(
    request: object, tag_name: str, tag_description: str, object_type: str, object_id: int
) -> Tag:
    tag = create_tag(request, tag_name, tag_description)
    obj = get_object_by_type_and_id(object_type, object_id)
    if isinstance(obj, TaggableMixin):
        obj.add_tag(tag)
        logger.info(f"Added {tag} to {obj}")
    else:
        logger.warning(f"Object {obj} is not taggable. Created tag {tag} but did not add it to the object.")
    return tag


"""
====================================================================
MANAGEMENT
====================================================================
"""


def create_tenant(request: object, name: str):
    tenant = Tenant.objects.create(tenant_name=name)
    logger.info(f"Tenant created: {tenant}")
    return tenant


def create_tenant_user_member(request: object, tenant_id: int, user_id: int, role: str) -> TenantUserMember:
    tenant_user = TenantUserMember.objects.create(tenant_id=tenant_id, user_id=user_id, role=role)
    logger.info(f"TenantUserMember created: {tenant_user}")
    return tenant_user


"""
====================================================================
FILTERS
====================================================================
"""


def create_rule(
    request: object,
    name: str,
    description: str,
    action: str,
    log_type: str,
    hit_count: int,
    enable: bool = True,
) -> Rule:
    tenant = get_current_tenant(request)
    now = datetime.now(timezone.utc)
    rule = Rule(
        name=name,
        description=description,
        tenant=tenant,
        action=action,
        log_type=log_type,
        hit_count=hit_count,
        date_created=now,
        date_changed=now,
        created_by=request.user.id if hasattr(request, "user") else None,
        changed_by=request.user.id if hasattr(request, "user") else None,
        enable=enable,
    )
    try:
        rule.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Rule validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    rule.save()
    logger.info(f"Created {rule} for tenant={rule.tenant_id}")
    return rule


def create_filter(
    request: object,
    name: str,
    description: str,
    enable: bool = False,
) -> Filter:
    tenant_id = get_current_tenant_id(request)
    filter_obj = Filter(
        name=name,
        description=description,
        tenant_id=tenant_id,
        enable=enable,
    )
    try:
        filter_obj.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Filter validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    filter_obj.save()
    logger.info(f"Created {filter_obj} for tenant={filter_obj.tenant_id}")
    return filter_obj


"""
====================================================================
POLICY GENERATION
====================================================================
"""


def create_policy_rule_from_rule_match(rule_match: RuleMatch, sequence: int) -> PolicyRule:
    rule = rule_match.rule
    obj = rule_match.object
    if not obj:
        raise ValueError(f"Object with ID {rule_match.object_id} does not exist for rule with ID {rule.id}.")
    model_name = rule_match.object_type.model

    if model_name not in ["address", "service", "addressgroup", "servicegroup"]:
        raise ValueError(f"Invalid object type {rule_match.object_type} for rule with ID {rule.id}.")

    policy_rule = PolicyRule(
        name=rule.name,
        obj_type=model_name,
        action=rule.action,
        object=obj,
        sequence=sequence,
        direction=rule_match.match,
    )
    return policy_rule


def create_policy_rules_from_rule_filter(rule_filter: RuleFilter) -> list[PolicyRule]:
    policy_rules = []
    if not rule_filter.rule.id:
        raise ValueError(f"Rule with ID {rule_filter.rule.id} does not exist.")
    # Get sequence from RuleFilter
    sequence = rule_filter.sequence
    if not sequence:
        raise ValueError(f"Sequence is not set for rule match with ID {rule_filter.id}.")

    # Get actual rule object from join on RuleFilter
    rule = Rule.objects.get(id=rule_filter.rule.id)
    if not rule:
        raise ValueError(f"Rule with ID {rule_filter.rule.id} does not exist.")

    # Join rule with objects using RuleMatch to retrieve the actual rules
    rule_matches = RuleMatch.objects.filter(rule=rule)
    if not rule_matches.exists():
        raise ValueError(f"No rule matches found for rule with ID {rule.id}.")
    for rule_match in rule_matches:
        policy_rules.append(create_policy_rule_from_rule_match(rule_match, sequence))
    return policy_rules


def create_policy_from_filter(request, filter_id, vendor, policy_type):

    # Get filter object by ID
    filter = Filter.objects.get(id=filter_id)
    if not filter:
        raise ValueError(f"Filter with ID {filter_id} does not exist.")

    # Join filter with rules using RuleFilter
    rule_filter_matches = RuleFilter.objects.filter(filter_id=filter)
    if not rule_filter_matches.exists():
        raise ValueError(f"No rule matches found for filter with ID {filter_id}.")

    # Create PolicyRule objects for each rule
    policy_rules = []
    for rule_filter in rule_filter_matches:
        policy_rules.extend(create_policy_rules_from_rule_filter(rule_filter))

    policy = Policy(
        name=filter.name,
        rules=policy_rules,
        vendor=vendor,
        policy_type=policy_type,
        request=request,
    )
    return policy


def create_device(request: object, name: str, platform: str, description: str, type: str) -> object:
    tenant_id = get_current_tenant_id(request)

    device = Device(
        name=name,
        platform=platform,
        type=type,
        description=description,
        tenant_id=tenant_id,
    )
    try:
        device.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Device validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    device.save()
    logger.info(f"Created {device} for tenant={device.tenant_id}")
    return device


def create_device_group(request: object, name: str, description: str) -> object:
    tenant_id = get_current_tenant_id(request)

    device_group = DeviceGroup(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    try:
        device_group.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Device Group validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    device_group.save()
    logger.info(f"Created {device_group} for tenant={device_group.tenant_id}")
    return device_group


def add_devices_to_group(device_group_id: int, device_ids: list[int]) -> dict:
    device_group = DeviceGroup.objects.get(id=device_group_id)

    requested_ids = set(device_ids)

    existing_devices = Device.objects.filter(id__in=requested_ids)
    found_ids = set(existing_devices.values_list("id", flat=True))
    not_found_ids = requested_ids - found_ids

    already_present_ids = set(
        DeviceGroupMember.objects.filter(
            device_group=device_group,
            device__id__in=found_ids,
        ).values_list("device__id", flat=True)
    )

    new_ids = found_ids - already_present_ids

    new_members = [DeviceGroupMember(device_group=device_group, device_id=device_id) for device_id in new_ids]

    with transaction.atomic():
        DeviceGroupMember.objects.bulk_create(new_members)

    added_ids = sorted(new_ids)

    return {
        "device_group_id": device_group.id,
        "added_device_ids": added_ids,
        "already_present_device_ids": sorted(already_present_ids),
        "not_found_device_ids": sorted(not_found_ids),
    }
