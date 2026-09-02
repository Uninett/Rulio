from typing import Any, Literal

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.device_group_member import DeviceGroupMember
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.services.helper_user_tenant import is_superadmin, require_write_tenant
from backend.services.update import update_filter_interface_sequence
from backend.utils.logger import set_up_logger
from constants import GLOBAL_TENANT_ID

logger = set_up_logger(__name__)


def _editable_tenant_ids(actor: User, tenant_id: int) -> list[int]:
    """
    Returns a list of tenant IDs that the actor can edit, including the specified tenant_id.
    If the actor is a superadmin, the global tenant ID is also included.
    """
    tenant_ids = [tenant_id]
    if getattr(actor, "is_superuser", False):
        tenant_ids.append(GLOBAL_TENANT_ID)
    return tenant_ids


def _reference_tenant_ids(tenant_id: int, *, include_global: bool = True) -> list[int]:
    """
    Returns a list of tenant IDs that can be referenced, including the specified tenant_id.
    If include_global is True, the global tenant ID is also included.
    Different from _editable_tenant_ids, this function does not require the actor to have write permissions, as it is used for reference purposes.
    """
    tenant_ids = [tenant_id]
    if include_global:
        tenant_ids.append(GLOBAL_TENANT_ID)
    return tenant_ids


def _validate_member_for_group(*, group_tenant_id: int, member_tenant_id: int, member_label: str) -> None:
    """
    Validates that a member can be added to a group based on tenant IDs.
    Raises PermissionDenied if the member cannot be added to the group.
    """
    if group_tenant_id == GLOBAL_TENANT_ID and member_tenant_id != GLOBAL_TENANT_ID:
        raise PermissionDenied(f"Cannot add tenant-scoped {member_label} to a global group.")


@transaction.atomic
def add_address_to_group(actor: User, tenant_id: int, address_group_id: int, address_id: int) -> None:
    require_write_tenant(actor, tenant_id)

    address_group = AddressGroup.objects.filter(
        id=address_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if address_group is None:
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")

    address = Address.objects.filter(
        id=address_id,
        tenant_id__in=_reference_tenant_ids(tenant_id),
    ).first()
    if address is None:
        raise PermissionDenied(f"Address with ID {address_id} does not exist in tenant {tenant_id}.")

    _validate_member_for_group(
        group_tenant_id=address_group.tenant_id,
        member_tenant_id=address.tenant_id,
        member_label="addresses",
    )

    _, created = AddressGroupMember.objects.get_or_create(
        group=address_group,
        address=address,
    )

    if created:
        logger.info("Added address id=%s to address group id=%s.", address_id, address_group_id)
    else:
        logger.info("Address id=%s is already a member of address group id=%s.", address_id, address_group_id)


@transaction.atomic
def add_service_to_group(actor: User, tenant_id: int, service_group_id: int, service_id: int) -> ServiceGroup:
    require_write_tenant(actor, tenant_id)

    service_group = ServiceGroup.objects.filter(
        id=service_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if service_group is None:
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")

    service = Service.objects.filter(
        id=service_id,
        tenant_id__in=_reference_tenant_ids(tenant_id),
    ).first()
    if service is None:
        raise PermissionDenied(f"Service with ID {service_id} does not exist in tenant {tenant_id}.")

    _validate_member_for_group(
        group_tenant_id=service_group.tenant_id,
        member_tenant_id=service.tenant_id,
        member_label="services",
    )

    _, created = ServiceGroupMember.objects.get_or_create(
        group=service_group,
        service=service,
    )

    if created:
        logger.info("Added service id=%s to service group id=%s.", service_id, service_group_id)
    else:
        logger.info("Service id=%s is already a member of service group id=%s.", service_id, service_group_id)

    return service_group


@transaction.atomic
def add_addresses_to_group(
    actor: User,
    tenant_id: int,
    address_group_id: int,
    address_ids: list[int],
    request_type: str | None = "standard",
) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    address_group = AddressGroup.objects.filter(
        id=address_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if address_group is None:
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")

    requested_address_ids = set(address_ids)
    addresses_by_id = {
        address.id: address
        for address in Address.objects.filter(
            id__in=requested_address_ids,
            tenant_id__in=_reference_tenant_ids(tenant_id),
        )
    }

    valid_address_ids = set(addresses_by_id.keys())
    invalid_address_ids = sorted(requested_address_ids - valid_address_ids)
    if invalid_address_ids:
        raise PermissionDenied(
            f"One or more addresses do not exist in tenant {tenant_id} or the global tenant. "
            f"Invalid address IDs: {invalid_address_ids}"
        )

    for address in addresses_by_id.values():
        _validate_member_for_group(
            group_tenant_id=address_group.tenant_id,
            member_tenant_id=address.tenant_id,
            member_label="addresses",
        )

    already_present_address_ids = set(
        AddressGroupMember.objects.filter(
            group_id=address_group.id,
            address_id__in=requested_address_ids,
        ).values_list("address_id", flat=True)
    )

    added_address_ids: list[int] = []

    for address_id in address_ids:
        if address_id in already_present_address_ids:
            continue

        AddressGroupMember.objects.create(
            group=address_group,
            address_id=address_id,
        )
        added_address_ids.append(address_id)
        already_present_address_ids.add(address_id)

    returned_already_present_address_ids = [
        address_id for address_id in address_ids if address_id not in added_address_ids
    ]

    if request_type != "seeding":
        logger.info(
            "Group %s: added=%s, already_present=%s, not_found=%s",
            address_group.id,
            added_address_ids,
            returned_already_present_address_ids,
            [],
        )

    return {
        "address_group_id": address_group.id,
        "added_address_ids": added_address_ids,
        "already_present_address_ids": returned_already_present_address_ids,
        "not_found_address_ids": [],
    }


@transaction.atomic
def remove_address_from_group(actor: User, tenant_id: int, address_group_id: int, address_id: int) -> None:
    """
    Legacy function to remove a single address from an address group. 
    For future always use remove_addresses_from_group when removing address(es) from a group.
    """
    require_write_tenant(actor, tenant_id)

    address_group = AddressGroup.objects.filter(
        id=address_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if address_group is None:
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")

    address = Address.objects.filter(
        id=address_id,
        tenant_id__in=_reference_tenant_ids(tenant_id),
    ).first()
    if address is None:
        raise PermissionDenied(f"Address with ID {address_id} does not exist in tenant {tenant_id}.")

    try:
        address_group_member = AddressGroupMember.objects.get(group=address_group, address=address)
        address_group_member.delete()
        logger.info("Removed address id=%s from address group id=%s.", address_id, address_group_id)
    except AddressGroupMember.DoesNotExist:
        logger.warning("Address id=%s is not a member of address group id=%s.", address_id, address_group_id)


@transaction.atomic
def remove_addresses_from_group(actor: User, tenant_id: int, address_group_id: int, address_ids: list[int]) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    address_group = AddressGroup.objects.filter(
        id=address_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if address_group is None:
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")

    if not address_ids:
        logger.info("No address IDs provided for removal from address group id=%s.", address_group_id)
        return {
            "address_group_id": address_group.id,
            "removed_count": 0,
        }

    for address_id in address_ids:
        address = Address.objects.filter(
            id=address_id,
            tenant_id__in=_reference_tenant_ids(tenant_id),
        ).first()
        if address is None:
            raise PermissionDenied(f"Address with ID {address_id} does not exist in tenant {tenant_id}.")

        _validate_member_for_group(
            group_tenant_id=address_group.tenant_id,
            member_tenant_id=address.tenant_id,
            member_label="addresses",
        )
    deleted_count, _ = AddressGroupMember.objects.filter(
        group=address_group,
        address__id__in=address_ids,
    ).delete()

    logger.info(
        "Removed %s addresses from Address Group %s.",
        deleted_count,
        address_group.id,
    )

    return {
        "address_group_id": address_group.id,
        "removed_count": deleted_count,
    }


@transaction.atomic
def add_services_to_group(
    actor: User,
    tenant_id: int,
    service_group_id: int,
    service_ids: list[int],
    request_type: str | None = "standard",
) -> dict[str, Any]:
    """
    Adds a list of services to a service group.

    Args:
    - service_group_id: ID of the service group to add services to
    - service_ids: List of service IDs to add to the group
    """
    require_write_tenant(actor, tenant_id)

    service_group = ServiceGroup.objects.filter(
        id=service_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if service_group is None:
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")

    requested_service_ids = set(service_ids)
    services_by_id = {
        service.id: service
        for service in Service.objects.filter(
            id__in=requested_service_ids,
            tenant_id__in=_reference_tenant_ids(tenant_id),
        )
    }

    valid_service_ids = set(services_by_id.keys())
    invalid_service_ids = sorted(requested_service_ids - valid_service_ids)
    if invalid_service_ids:
        raise PermissionDenied(
            f"One or more services do not exist in tenant {tenant_id} or the global tenant. "
            f"Invalid service IDs: {invalid_service_ids}"
        )

    for service in services_by_id.values():
        _validate_member_for_group(
            group_tenant_id=service_group.tenant_id,
            member_tenant_id=service.tenant_id,
            member_label="services",
        )

    existing_member_ids = set(
        ServiceGroupMember.objects.filter(
            group_id=service_group.id,
            service_id__in=requested_service_ids,
        ).values_list("service_id", flat=True)
    )

    added_service_ids: list[int] = []
    already_present_service_ids: list[int] = []

    for service_id in service_ids:
        if service_id in existing_member_ids:
            already_present_service_ids.append(service_id)
            continue

        ServiceGroupMember.objects.create(
            group=service_group,
            service_id=service_id,
        )
        added_service_ids.append(service_id)
        existing_member_ids.add(service_id)

    if request_type != "seeding":
        logger.info(
            "Group %s: added=%s, already_present=%s, not_found=%s",
            service_group.id,
            added_service_ids,
            already_present_service_ids,
            [],
        )

    return {
        "service_group_id": service_group.id,
        "added_service_ids": added_service_ids,
        "already_present_service_ids": already_present_service_ids,
        "not_found_service_ids": [],
    }


@transaction.atomic
def remove_service_from_group(actor: User, tenant_id: int, service_group_id: int, service_id: int) -> None:
    require_write_tenant(actor, tenant_id)

    service_group = ServiceGroup.objects.filter(
        id=service_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if service_group is None:
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")

    service = Service.objects.filter(
        id=service_id,
        tenant_id__in=_reference_tenant_ids(tenant_id),
    ).first()
    if service is None:
        raise PermissionDenied(f"Service with ID {service_id} does not exist in tenant {tenant_id}.")

    try:
        service_group_member = ServiceGroupMember.objects.get(group=service_group, service=service)
        service_group_member.delete()
        logger.info("Removed service id=%s from service group id=%s.", service_id, service_group_id)
    except ServiceGroupMember.DoesNotExist:
        logger.warning("Service id=%s is not a member of service group id=%s.", service_id, service_group_id)


@transaction.atomic
def add_objects_to_rule(
    *,
    actor: User,
    tenant_id: int,
    rule_id: int,
    match_type: str,
    objects: list,
    request_type: str | None = "standard",
) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    rule = Rule.objects.filter(
        id=rule_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if rule is None:
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")

    added: list[dict[str, Any]] = []
    already_exists: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for obj in objects:
        try:
            if obj.tenant_id not in (GLOBAL_TENANT_ID, rule.tenant_id):
                errors.append(
                    {
                        "object_id": obj.id,
                        "reason": (
                            f"Object {obj.id}, Name {obj.name} does not belong to tenant {rule.tenant_id} "
                            "and is not global"
                        ),
                    }
                )
                continue

            content_type = ContentType.objects.get_for_model(obj)

            rule_match, created = RuleMatch.objects.get_or_create(
                rule=rule,
                match=match_type,
                object_type=content_type,
                object_id=obj.id,
            )

            payload = {
                "object_id": obj.id,
                "name": getattr(obj, "name", str(obj)),
                "match": match_type,
            }

            if created:
                if request_type != "seeding":
                    logger.info("Created RuleMatch: %s", rule_match)
                added.append(payload)
            else:
                if request_type != "seeding":
                    logger.info("RuleMatch already exists: %s", rule_match)
                already_exists.append(payload)

        except Exception as exc:
            errors.append(
                {
                    "object_id": getattr(obj, "id", None),
                    "reason": str(exc),
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


@transaction.atomic
def update_objects_in_rule(
    *, actor: User, tenant_id: int, rule_id: int, match_type: str, objects: list
) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    rule = Rule.objects.filter(
        id=rule_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if rule is None:
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")

    RuleMatch.objects.filter(rule=rule, match=match_type).delete()

    return add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_id,
        match_type=match_type,
        objects=objects,
    )

@transaction.atomic
def remove_objects_from_rule(
    *, actor: User, tenant_id: int, rule_id: int, match_type: str, object_ids: list[int]
) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    rule = Rule.objects.filter(
        id=rule_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if rule is None:
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")

    for object_id in object_ids:
        if not RuleMatch.objects.filter(rule=rule, match=match_type, object_id=object_id).exists():
            raise PermissionDenied(
                f"Object with ID {object_id} is not associated with Rule {rule_id} and match_type {match_type}."
            )

    deleted_count, _ = RuleMatch.objects.filter(rule=rule, match=match_type, object_id__in=object_ids).delete()

    logger.info(
        "Removed %s objects from Rule %s with match_type %s.",
        deleted_count,
        rule.id,
        match_type,
    )

    return {
        "rule_id": rule_id,
        "match_type": match_type,
        "removed_count": deleted_count,
    }


@transaction.atomic
def copy_rule_to_filter(*, actor: User, tenant_id: int, rule_id: int, filter_id: int, rule_sequence: int) -> Rule:
    require_write_tenant(actor, tenant_id)

    source_rule = Rule.objects.filter(
        id=rule_id,
        tenant_id__in=_reference_tenant_ids(tenant_id),
    ).first()
    if source_rule is None:
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")

    filter_obj = Filter.objects.filter(
        id=filter_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if filter_obj is None:
        raise PermissionDenied(f"Filter with ID {filter_id} does not exist in tenant {tenant_id}.")

    new_rule = Rule.objects.create(
        name=f"{source_rule.name}_copy",
        description=source_rule.description,
        filter=filter_obj,
        tenant=source_rule.tenant,
        action=source_rule.action,
        enable=source_rule.enable,
        rule_sequence=rule_sequence,
        log_type=source_rule.log_type,
        hit_count=0,
        created_by=actor.id,
        changed_by=actor.id,
    )

    logger.info(
        "Copied Rule %s to new Rule %s in Filter %s with rule_sequence %s",
        source_rule.id,
        new_rule.id,
        filter_obj.id,
        rule_sequence,
    )
    return new_rule


@transaction.atomic
def add_filter_to_interface(
    *,
    actor: User,
    tenant_id: int,
    filter_id: int,
    interface_id: int,
    policy_sequence: int,
    enable: bool,
    direction: Literal["in", "out"],
):
    require_write_tenant(actor, tenant_id)

    filter_obj = Filter.objects.filter(
        id=filter_id,
        tenant_id__in=_reference_tenant_ids(tenant_id),
    ).first()
    if filter_obj is None:
        raise PermissionDenied(f"Filter with ID {filter_id} does not exist in tenant {tenant_id}.")

    interface = Interface.objects.filter(id=interface_id, device__tenant_id__in=_editable_tenant_ids(actor, tenant_id)).first()
    if interface is None:
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")

    interface_direction = InterfaceDirection.objects.get(interface=interface, direction=direction)
    filter_interface, created = interface.filterinterface_set.get_or_create(
        interface_direction=interface_direction,
        filter=filter_obj,
        defaults={"policy_sequence": 0, "direction": direction, "enable": enable},
    )

    filter_interface.direction = direction
    filter_interface.enable = enable
    filter_interface.save()

    update_filter_interface_sequence(
        actor=actor,
        tenant_id=tenant_id,
        filter_interface=filter_interface,
        new_sequence=policy_sequence,
    )

    filter_interface.refresh_from_db()

    if not created:
        logger.info(
            "Updated Filter %s on Interface %s with policy_sequence %s and enable %s",
            filter_obj.id,
            interface.id,
            filter_interface.policy_sequence,
            enable,
        )
    else:
        logger.info(
            "Added Filter %s to Interface %s with policy_sequence %s and enable %s",
            filter_obj.id,
            interface.id,
            filter_interface.policy_sequence,
            enable,
        )

    return interface, filter_obj

@transaction.atomic
def remove_filters_from_interface(
    *,
    actor: User,
    tenant_id: int,
    filter_ids: list[int],
    interface_id: int,
    direction: Literal["in", "out"],
):
    require_write_tenant(actor, tenant_id)

    for filter_id in filter_ids:
        filter_obj = Filter.objects.filter(
            id=filter_id,
            tenant_id__in=_reference_tenant_ids(tenant_id),
        ).first()
        if filter_obj is None:
            raise PermissionDenied(f"Filter with ID {filter_id} does not exist in tenant {tenant_id}.")

    interface = Interface.objects.filter(id=interface_id, device__tenant_id=tenant_id).first()
    if interface is None:
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")

    for filter_id in filter_ids:
        filter_obj = Filter.objects.get(id=filter_id)
        interface_direction = InterfaceDirection.objects.get(interface=interface, direction=direction)
        deleted_count, _ = interface.filterinterface_set.filter(
            interface_direction=interface_direction,
            filter=filter_obj,
        ).delete()
        if deleted_count == 0:
            logger.warning(
                "Filter %s was not associated with Interface %s in direction %s.",
                filter_obj.id,
                interface.id,
                direction,
            )
        else:
            update_filter_interface_sequence(
                actor=actor,
                tenant_id=tenant_id,
                filter_interface=None,
                new_sequence=None,
            )

    logger.info(
        "Removed Filter %s from Interface %s in direction %s.",
        filter_obj.id,
        interface.id,
        direction,
    )


@transaction.atomic
def add_devices_to_group(*, actor: User, tenant_id: int, device_group_id: int, device_ids: list[int]) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    device_group = DeviceGroup.objects.filter(id=device_group_id, tenant_id=tenant_id).first()
    if device_group is None:
        raise PermissionDenied(f"Device group with ID {device_group_id} does not exist in tenant {tenant_id}.")

    requested_ids = set(device_ids)
    existing_devices = Device.objects.filter(id__in=requested_ids, tenant_id=tenant_id)
    found_ids = set(existing_devices.values_list("id", flat=True))
    not_found_ids = requested_ids - found_ids

    if not_found_ids:
        raise PermissionDenied(
            f"One or more devices do not exist in tenant {tenant_id}. Invalid device IDs: {sorted(not_found_ids)}"
        )

    already_present_ids = set(
        DeviceGroupMember.objects.filter(
            device_group=device_group,
            device__id__in=found_ids,
        ).values_list("device__id", flat=True)
    )

    new_ids = found_ids - already_present_ids
    new_members = [DeviceGroupMember(device_group=device_group, device_id=device_id) for device_id in new_ids]

    DeviceGroupMember.objects.bulk_create(new_members)

    added_ids = sorted(new_ids)

    return {
        "device_group_id": device_group.id,
        "added_device_ids": added_ids,
        "already_present_device_ids": sorted(already_present_ids),
        "not_found_device_ids": [],
    }

@transaction.atomic
def remove_devices_from_group(*, actor: User, tenant_id: int, device_group_id: int, device_ids: list[int]) -> dict[str, Any]:
    require_write_tenant(actor, tenant_id)

    device_group = DeviceGroup.objects.filter(id=device_group_id, tenant_id=tenant_id).first()
    if device_group is None:
        raise PermissionDenied(f"Device group with ID {device_group_id} does not exist in tenant {tenant_id}.")

    for device_id in device_ids:
        if not Device.objects.filter(id=device_id, tenant_id=tenant_id).exists():
            raise PermissionDenied(f"Device with ID {device_id} does not exist in tenant {tenant_id}.")

        deleted_count, _ = DeviceGroupMember.objects.filter(
            device_group=device_group,
            device__id=device_id,
        ).delete()

        if deleted_count == 0:
            logger.warning(
                "Device %s was not associated with Device Group %s.",
                device_id,
                device_group.id,
            )

    logger.info(
        "Removed %s devices from Device Group %s.",
        deleted_count,
        device_group.id,
    )

    return {
        "device_group_id": device_group.id,
        "removed_count": deleted_count,
    }


@transaction.atomic
def add_tag_to_object(
    *,
    actor: User,
    tenant_id: int,
    tag: Tag,
    obj: object,
    include_global: bool = True,
    request_type: str | None = "standard",
) -> None:
    require_write_tenant(actor, tenant_id)

    permitted_tenant_ids = _reference_tenant_ids(tenant_id, include_global=include_global)
    if not Tag.objects.filter(id=tag.id, tenant_id__in=permitted_tenant_ids).exists() and not is_superadmin(actor):
        raise PermissionDenied(f"Tag with ID {tag.id} does not exist in tenant {tenant_id}.")

    content_type = ContentType.objects.get_for_model(obj)

    if TagConnection.objects.filter(tag=tag, content_type=content_type, object_id=obj.id).exists():
        if request_type != "seeding":
            logger.info("Tag %s is already associated with object %s.", tag.id, obj)
        return

    TagConnection.objects.create(tag=tag, content_object=obj)

    if request_type != "seeding":
        logger.info("Added tag %s to object %s.", tag.id, obj)

@transaction.atomic
def remove_tag_from_object(
    *,
    actor: User,
    tenant_id: int,
    tag_id: int,
    obj: object,
    include_global: bool = True,
) -> int:
    require_write_tenant(actor, tenant_id)

    permitted_tenant_ids = _reference_tenant_ids(tenant_id, include_global=include_global)
    if not Tag.objects.filter(id=tag_id, tenant_id__in=permitted_tenant_ids).exists() and not is_superadmin(actor):
        raise PermissionDenied(f"Tag with ID {tag_id} does not exist in tenant {tenant_id}.")

    content_type = ContentType.objects.get_for_model(obj)
    deleted_count, _ = TagConnection.objects.filter(tag_id=tag_id, content_type=content_type, object_id=obj.id).delete()

    logger.info("Removed tag %s from object %s. Deleted connections: %s.", tag_id, obj, deleted_count)

    return deleted_count