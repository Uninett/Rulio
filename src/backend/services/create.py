from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from django.core.exceptions import ValidationError as DjangoValidationError

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.filters.rule_filter import RuleFilter
from backend.objects.management.tenant import Tenant
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.objects.attributes.tag import Tag
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.filters.rule import Rule
from backend.schemas import rule
from backend.services.generate_config import Policy, PolicyRule, generate_config
from backend.utils.logger import set_up_logger
from backend.services.get import get_object_by_type_and_id
from backend.services.membership import (
    add_addresses_to_group,
    add_services_to_group,
)

from django.contrib.contenttypes.models import ContentType


# Setup logger
logger = set_up_logger(__name__)


# This is a temporary solution for tenant ID management. In a real implementation, this would be handled by an authentication system and middleware that sets the tenant ID in the request context.
def get_current_tenant_id(request: object) -> int:
    tenant_id = request.session.get("current_tenant_id")
    if tenant_id is None:
        logger.warning("Tenant ID not set in request session.")
        raise Exception("Tenant ID not set in request. Please call /set_tenant first.")
    try:
        return int(tenant_id)
    except ValueError:
        logger.warning(f"Invalid tenant ID in session: {tenant_id}")
        raise Exception(f"Invalid tenant ID in session: {tenant_id}")


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


def create_tenant(request: object, name: str):
    tenant = Tenant.objects.create(tenant_name=name)
    logger.info(f"Tenant created: {tenant}")
    return tenant


def create_tenant_user_member(request: object, tenant_id: int, user_id: int, role: str) -> TenantUserMember:
    tenant_user = TenantUserMember.objects.create(tenant_id=tenant_id, user_id=user_id)
    logger.info(f"TenantUserMember created: {tenant_user}")
    return tenant_user


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


def create_rule(
    request: object,
    name: str,
    description: str,
    tenant_id: int,
    action: str,
    log_type: str,
    hit_count: int,
    enable: bool = True,
) -> Rule:
    tenant = Tenant.objects.get(pk=tenant_id)
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


def match_rule_to_objects(
    request: object, #why not a request?
    rule_id: int,
    match_type: str,
    object_type: str,
    object_ids: list[int],
):
    rule = Rule.objects.get(id=rule_id)

    added = []
    already_exists = []
    errors = []

    for object_id in object_ids:
        try:
            obj = get_object_by_type_and_id(object_type, object_id)

            if obj.tenant_id not in (0, rule.tenant_id):
                errors.append(
                    {
                        "object_id": object_id,
                        "reason": f"Object {obj.id}, Name {obj.name} does not belong to tenant {rule.tenant_id} and is not global",
                    }
                )
                continue

            content_type = ContentType.objects.get_for_model(obj)

            rule_match, created = RuleMatch.objects.get_or_create(
                rule=rule,
                match=match_type,
                content_type=content_type,
                object_id=obj.id,
            )

            if created:
                rule.increment_hit_count()
                added.append(
                    {
                        "object_id": obj.id,
                        "name": getattr(obj, "name", str(obj)),
                        "match": match_type,
                    }
                )
            else:
                already_exists.append(
                    {
                        "object_id": obj.id,
                        "name": getattr(obj, "name", str(obj)),
                        "match": match_type,
                    }
                )

        except Exception as e:
            errors.append(
                {
                    "object_id": object_id,
                    "reason": str(e),
                }
            )

    return {
        "rule_id": rule_id,
        "added": added,
        "already_exists": already_exists,
        "errors": errors,
        "added_count": len(added),
        "already_exists_count": len(already_exists),
        "error_count": len(errors),
    }

def create_config_from_filter(request, filter_id, vendor, policy_type):
    filter_obj = get_object_by_type_and_id("filter", filter_id)
    if not filter_obj:
        raise ValueError(f"Filter with ID {filter_id} does not exist.")

    rule_filter_matches = RuleFilter.objects.filter(rule=filter_obj)
    if not rule_filter_matches.exists():
        raise ValueError(f"No rule matches found for filter with ID {filter_id}.")
    policy_rules = []
    for rule_filter in rule_filter_matches:
        if not rule_filter.rule_id:
            raise ValueError(f"Rule with ID {rule_filter.rule_id} does not exist.")
        sequence = rule_filter.sequence
        if not sequence:
            raise ValueError(f"Sequence is not set for rule match with ID {rule_filter.id}.")
        rule = Rule.objects.get(id=rule_filter.rule_id.id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_filter.rule_id.id} does not exist.")
        object_type = rule.object_type.lower() if rule.object_type else None
        object_id = rule.object_id
        if not object_type or not object_id:
            raise ValueError(f"Object type or object ID is not set for rule with ID {rule.id}.")
        if object_type not in ["address", "service", "address_group", "service_group"]:
            raise ValueError(f"Invalid object type {object_type} for rule with ID {rule.id}.")
        match object_type:
            case "address":
                obj = Address.objects.get(id=object_id)
            case "service":
                obj = Service.objects.get(id=object_id)
            case "address_group":
                obj = AddressGroup.objects.get(id=object_id)
            case "service_group":
                obj = ServiceGroup.objects.get(id=object_id)
        if not obj:
            raise ValueError(f"Object with ID {object_id} does not exist for rule with ID {rule.id}.")
        policy_rule = PolicyRule(
            name=rule.name,
            obj_type=object_type,
            action=rule.action,
            object=obj,
            sequence=sequence,
            direction=rule.direction,
        )
        policy_rules.append(policy_rule)
    policy = Policy(
        name=filter_obj.name,
        rules=policy_rules,
        vendor=vendor,
        policy_type=policy_type,
        request=request,
    )

    config = generate_config(policy)
    return config



        
