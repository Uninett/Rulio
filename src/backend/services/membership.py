from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied


from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.address import Address
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_filter import RuleFilter
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.device_group_member import DeviceGroupMember
from backend.objects.tenant_objects.interface import Interface
from backend.services.helper_user_tenant import is_superadmin, require_write_tenant
from backend.utils.logger import set_up_logger
from constants import GLOBAL_TENANT_ID

logger = set_up_logger(__name__)


def add_address_to_group(actor: User, tenant_id: int, address_group_id: int, address_id: int):
    require_write_tenant(actor, tenant_id)
    if not AddressGroup.objects.filter(id=address_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")
    if not (
        Address.objects.filter(id=address_id, tenant_id=tenant_id).exists()
        or Address.objects.filter(id=address_id, tenant_id=GLOBAL_TENANT_ID).exists()
    ):
        raise PermissionDenied(f"Address with ID {address_id} does not exist in tenant {tenant_id}.")
    _address_group = AddressGroup.objects.get(id=address_group_id)
    _address = Address.objects.get(id=address_id)
    _address_group_member = AddressGroupMember.objects.create(
        group=_address_group,
        address=_address,
    )


def add_service_to_group(actor: User, tenant_id: int, service_group_id: int, service_id: int) -> ServiceGroup:
    require_write_tenant(actor, tenant_id)
    if not ServiceGroup.objects.filter(id=service_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")
    if not (
        Service.objects.filter(id=service_id, tenant_id=tenant_id).exists()
        or Service.objects.filter(id=service_id, tenant_id=GLOBAL_TENANT_ID).exists()
    ):
        raise PermissionDenied(f"Service with ID {service_id} does not exist in tenant {tenant_id}.")
    _service_group = ServiceGroup.objects.get(id=service_group_id)
    _service = Service.objects.get(id=service_id)
    _service_group_member = ServiceGroupMember.objects.create(
        group=_service_group,
        service=_service,
    )


def add_addresses_to_group(actor: User, tenant_id: int, address_group_id: int, address_ids: list[int]) -> dict:
    require_write_tenant(actor, tenant_id)

    if not AddressGroup.objects.filter(id=address_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")

    address_group = AddressGroup.objects.get(id=address_group_id, tenant_id=tenant_id)

    requested_address_ids = set(address_ids)
    valid_address_ids = set(
        Address.objects.filter(
            id__in=requested_address_ids,
            tenant_id__in=[tenant_id, GLOBAL_TENANT_ID],
        ).values_list("id", flat=True)
    )

    invalid_address_ids = sorted(requested_address_ids - valid_address_ids)
    if invalid_address_ids:
        raise PermissionDenied(
            f"One or more addresses do not exist in tenant {tenant_id} or the global tenant. "
            f"Invalid address IDs: {invalid_address_ids}"
        )

    already_present_address_ids = set(
        AddressGroupMember.objects.filter(
            group_id=address_group_id,
            address_id__in=requested_address_ids,
        ).values_list("address_id", flat=True)
    )

    added_address_ids = []

    with transaction.atomic():
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
        address_id for address_id in address_ids if address_id in (set(address_ids) - set(added_address_ids))
    ]

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


def add_services_to_group(actor: User, tenant_id: int, service_group_id: int, service_ids: list[int]) -> dict:
    """
    Adds a list of services to a service group.

    Args:
    - service_group_id: ID of the service group to add services to
    - service_ids: List of service IDs to add to the group
    """
    require_write_tenant(actor, tenant_id)

    if not ServiceGroup.objects.filter(id=service_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")

    service_group = ServiceGroup.objects.get(id=service_group_id, tenant_id=tenant_id)

    requested_service_ids = set(service_ids)
    # Validate that all requested service IDs exist in the tenant or global tenant
    valid_service_ids = set(
        Service.objects.filter(
            id__in=requested_service_ids,
            tenant_id__in=[tenant_id, GLOBAL_TENANT_ID],
        ).values_list("id", flat=True)
    )

    invalid_service_ids = sorted(requested_service_ids - valid_service_ids)
    if invalid_service_ids:
        raise PermissionDenied(
            f"One or more services do not exist in tenant {tenant_id} or the global tenant. "
            f"Invalid service IDs: {invalid_service_ids}"
        )

    existing_member_ids = set(
        ServiceGroupMember.objects.filter(
            group_id=service_group_id,
            service_id__in=requested_service_ids,
        ).values_list("service_id", flat=True)
    )

    added_service_ids = []
    already_present_service_ids = []

    for service_id in service_ids:
        if service_id in existing_member_ids:
            already_present_service_ids.append(service_id)
        else:
            ServiceGroupMember.objects.create(
                group=service_group,
                service_id=service_id,
            )
            added_service_ids.append(service_id)
            existing_member_ids.add(service_id)

    logger.info(
        "Group %s: added=%s, already_present=%s, not_found=%s",
        service_group_id,
        added_service_ids,
        already_present_service_ids,
        [],
    )

    return {
        "service_group_id": service_group_id,
        "added_service_ids": added_service_ids,
        "already_present_service_ids": already_present_service_ids,
        "not_found_service_ids": [],
    }


def add_objects_to_rule(
    *,
    actor: User,
    tenant_id: int,
    rule_id: int,
    match_type: str,
    objects: list,
):
    require_write_tenant(actor, tenant_id)
    if not Rule.objects.filter(id=rule_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")
    rule = Rule.objects.get(id=rule_id)

    added = []
    already_exists = []
    errors = []

    for obj in objects:
        try:
            if obj.tenant_id not in (0, rule.tenant_id):
                errors.append(
                    {
                        "object_id": obj.id,
                        "reason": f"Object {obj.id}, Name {obj.name} does not belong to tenant {rule.tenant_id} and is not global",
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

            if created:
                logger.info(f"Created RuleMatch: {rule_match}")
                rule.increment_hit_count()
                added.append(
                    {
                        "object_id": obj.id,
                        "name": getattr(obj, "name", str(obj)),
                        "match": match_type,
                    }
                )
            else:
                logger.warning(f"RuleMatch already exists: {rule_match}")
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
                    "object_id": obj.id,
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


def add_rule_to_filter(*, actor: User, tenant_id: int, rule_id: int, filter_id: int, rule_sequence: int):
    require_write_tenant(actor, tenant_id)
    if not Rule.objects.filter(id=rule_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")
    rule = Rule.objects.get(id=rule_id)
    filter = Filter.objects.get(id=filter_id)

    rule_filter, created = RuleFilter.objects.get_or_create(
        rule=rule,
        filter=filter,
        defaults={"rule_sequence": rule_sequence},
    )

    if not created:
        rule_filter.rule_sequence = rule_sequence
        rule_filter.save()

    logger.info(f"Added Rule {rule.id} to Filter {filter.id} with rule_sequence {rule_sequence}")
    return rule_filter


def add_filter_to_interface(
    *, actor: User, tenant_id: int, filter_id: int, interface_id: int, policy_sequence: int, enable: bool
):
    require_write_tenant(actor, tenant_id)
    if not (
        Filter.objects.filter(id=filter_id, tenant_id=tenant_id).exists()
        or Filter.objects.filter(id=filter_id, tenant_id=GLOBAL_TENANT_ID).exists()
    ):
        raise PermissionDenied(f"Filter with ID {filter_id} does not exist in tenant {tenant_id}.")
    if not Interface.objects.filter(id=interface_id, device__tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")
    filter = Filter.objects.get(id=filter_id)
    interface = Interface.objects.get(id=interface_id)

    filter_interface, created = interface.filterinterface_set.get_or_create(
        interface=interface,
        filter=filter,
        defaults={"policy_sequence": policy_sequence, "enable": enable},
    )

    if not created:
        filter_interface.policy_sequence = policy_sequence
        filter_interface.enable = enable
        filter_interface.save()
        logger.warning(
            f"Updated Filter {filter.id} on Interface {interface.id} with policy_sequence {policy_sequence} and enable {enable}"
        )
    else:
        logger.info(
            f"Added Filter {filter.id} to Interface {interface.id} with policy_sequence {policy_sequence} and enable {enable}"
        )

    return interface, filter


def add_devices_to_group(*, actor: User, tenant_id: int, device_group_id: int, device_ids: list[int]) -> dict:
    require_write_tenant(actor, tenant_id)
    if not DeviceGroup.objects.filter(id=device_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Device group with ID {device_group_id} does not exist in tenant {tenant_id}.")
    if not Device.objects.filter(id__in=device_ids, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"One or more devices do not exist in tenant {tenant_id}.")
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


def add_tag_to_object(*, actor: User, tenant_id: int, tag: Tag, obj: object):
    require_write_tenant(actor, tenant_id)
    if not Tag.objects.filter(id=tag.id, tenant_id=tenant_id).exists() and not is_superadmin(actor):
        raise PermissionDenied(f"Tag with ID {tag.id} does not exist in tenant {tenant_id}.")
    if TagConnection.objects.filter(
        tag=tag, content_type=ContentType.objects.get_for_model(obj), object_id=obj.id
    ).exists():
        logger.warning(f"Tag {tag.id} is already associated with object {obj}.")
        return
    TagConnection.objects.create(tag=tag, content_object=obj)
