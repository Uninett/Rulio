from django.core.exceptions import PermissionDenied
from django.db import transaction

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.objects.tenant_objects.interface import Interface
from backend.services.helper_user_tenant import require_write_tenant
from constants import GLOBAL_TENANT_ID


def _editable_tenant_ids(actor, tenant_id: int) -> list[int]:
    tenant_ids = [tenant_id]
    if getattr(actor, "is_superuser", False):
        tenant_ids.append(GLOBAL_TENANT_ID)
    return tenant_ids


@transaction.atomic
def update_address(
    *,
    actor,
    tenant_id,
    address_id,
    name=None,
    description=None,
    addr_type=None,
    ipv4_type=None,
    ipv6_type=None,
    ipv4Network=None,
    ipv6Network=None,
    ipv4Address_start=None,
    ipv4Address_end=None,
    ipv6Address_start=None,
    ipv6Address_end=None,
):
    require_write_tenant(actor, tenant_id)

    address = Address.objects.filter(id=address_id, tenant_id__in=_editable_tenant_ids(actor, tenant_id)).first()
    if address is None:
        raise PermissionDenied(f"Address with ID {address_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        address.name = name
    if description is not None:
        address.description = description
    if addr_type is not None:
        address.addr_type = addr_type
    if ipv4_type is not None:
        address.ipv4_type = ipv4_type
    if ipv6_type is not None:
        address.ipv6_type = ipv6_type
    if ipv4Network is not None:
        address.ipv4Network = ipv4Network
    if ipv6Network is not None:
        address.ipv6Network = ipv6Network
    if ipv4Address_start is not None:
        address.ipv4Address_start = ipv4Address_start
    if ipv4Address_end is not None:
        address.ipv4Address_end = ipv4Address_end
    if ipv6Address_start is not None:
        address.ipv6Address_start = ipv6Address_start
    if ipv6Address_end is not None:
        address.ipv6Address_end = ipv6Address_end
    if ipv4_type == "remove":
        address.ipv4_type = None
        address.ipv4Network = None
        address.ipv4Address_start = None
        address.ipv4Address_end = None
    if ipv6_type == "remove":
        address.ipv6_type = None
        address.ipv6Network = None
        address.ipv6Address_start = None
        address.ipv6Address_end = None

    address.save()
    return address


@transaction.atomic
def update_service(
    *,
    actor,
    tenant_id,
    service_id,
    name=None,
    description=None,
    protocol=None,
    port_start=None,
    port_end=None,
    service_type=None,
):
    require_write_tenant(actor, tenant_id)

    service = Service.objects.filter(id=service_id, tenant_id__in=_editable_tenant_ids(actor, tenant_id)).first()
    if service is None:
        raise PermissionDenied(f"Service with ID {service_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        service.name = name
    if description is not None:
        service.description = description
    if protocol is not None:
        service.protocol = protocol
    if port_start is not None:
        service.port_start = port_start
    if port_end is not None:
        service.port_end = port_end
    if service_type is not None:
        service.service_type = service_type

    service.save()
    return service


@transaction.atomic
def update_address_group(*, actor, tenant_id, address_group_id, name=None, description=None, addr_type=None):
    require_write_tenant(actor, tenant_id)

    address_group = AddressGroup.objects.filter(
        id=address_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if address_group is None:
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        address_group.name = name
    if description is not None:
        address_group.description = description
    if addr_type is not None and addr_type.lower() != "group":
        raise ValueError("Address group type must be 'group'.")

    address_group.save()
    return address_group


@transaction.atomic
def update_service_group(*, actor, tenant_id, service_group_id, name=None, description=None, service_type=None):
    require_write_tenant(actor, tenant_id)

    service_group = ServiceGroup.objects.filter(
        id=service_group_id,
        tenant_id__in=_editable_tenant_ids(actor, tenant_id),
    ).first()
    if service_group is None:
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        service_group.name = name
    if description is not None:
        service_group.description = description
    if service_type is not None and service_type.lower() != "group":
        raise ValueError("Service group type must be 'group'.")

    service_group.save()
    return service_group


@transaction.atomic
def update_device(*, actor, tenant_id, device_id, name=None, description=None, platform=None, type=None):
    require_write_tenant(actor, tenant_id)

    device = Device.objects.filter(id=device_id, tenant_id=tenant_id).first()
    if device is None:
        raise PermissionDenied(f"Device with ID {device_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        device.name = name
    if description is not None:
        device.description = description
    if platform is not None:
        device.platform = platform
    if type is not None:
        device.type = type

    device.save()
    return device


@transaction.atomic
def update_device_group(*, actor, tenant_id, device_group_id, name=None, description=None):
    require_write_tenant(actor, tenant_id)

    device_group = DeviceGroup.objects.filter(id=device_group_id, tenant_id=tenant_id).first()
    if device_group is None:
        raise PermissionDenied(f"Device group with ID {device_group_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        device_group.name = name
    if description is not None:
        device_group.description = description

    device_group.save()
    return device_group


@transaction.atomic
def update_tag(*, actor, tenant_id, tag_id, name=None, description=None, color=None):
    require_write_tenant(actor, tenant_id)

    tag = Tag.objects.filter(id=tag_id, tenant_id__in=_editable_tenant_ids(actor, tenant_id)).first()
    if tag is None:
        raise PermissionDenied(f"Tag with ID {tag_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        tag.name = name
    if description is not None:
        tag.description = description
    if color is not None:
        tag.color = color

    tag.save()
    return tag


@transaction.atomic
def update_interface(*, actor, tenant_id, interface_id, name=None, description=None, type=None, VRF=None):
    require_write_tenant(actor, tenant_id)

    interface = Interface.objects.select_related("device").filter(id=interface_id, device__tenant_id=tenant_id).first()
    if interface is None:
        raise PermissionDenied(f"Interface with ID {interface_id} does not belong to tenant {tenant_id}.")

    if name is not None:
        interface.name = name
    if description is not None:
        interface.description = description
    if type is not None:
        interface.type = type
    if VRF is not None:
        interface.VRF = VRF

    interface.save()
    return interface


@transaction.atomic
def update_filter(*, actor, tenant_id, filter_id, name=None, description=None):
    require_write_tenant(actor, tenant_id)

    filter_obj = Filter.objects.filter(id=filter_id, tenant_id__in=_editable_tenant_ids(actor, tenant_id)).first()
    if filter_obj is None:
        raise PermissionDenied(f"Filter with ID {filter_id} does not exist in tenant {tenant_id}.")

    if name is not None:
        filter_obj.name = name
    if description is not None:
        filter_obj.description = description

    filter_obj.save()
    return filter_obj


@transaction.atomic
def update_filter_interface_sequence(*, actor, tenant_id, filter_interface, new_sequence):
    require_write_tenant(actor, tenant_id)

    if filter_interface.filter_id is None:
        raise ValueError("FilterInterface must be linked to a filter before updating its sequence.")

    filter_interface = (
        FilterInterface.objects.select_related("filter", "interface_direction__interface__device")
        .filter(
            id=filter_interface.id,
            filter__tenant_id__in=_editable_tenant_ids(actor, tenant_id),
        )
        .first()
    )
    if filter_interface is None:
        raise PermissionDenied("Filter interface does not exist in the current tenant scope.")

    interface_direction = filter_interface.interface_direction
    matching_filter_interfaces = FilterInterface.objects.filter(interface_direction=interface_direction).order_by(
        "policy_sequence"
    )
    is_placeholder = filter_interface.policy_sequence == 0

    if new_sequence is None:
        new_sequence = filter_interface.policy_sequence
    if new_sequence == 0:
        new_sequence = (
            matching_filter_interfaces.exclude(id=filter_interface.id).count()
            if is_placeholder
            else matching_filter_interfaces.count()
        ) + 1

    if is_placeholder:
        sibling_filter_interfaces = matching_filter_interfaces.exclude(id=filter_interface.id)
        if not sibling_filter_interfaces.exists():
            if new_sequence != 1:
                raise ValueError(
                    f"There are no filters attached to interface direction {interface_direction.id}, so the only valid sequence is 1."
                )
            filter_interface.policy_sequence = new_sequence
            filter_interface.save()
            return filter_interface

        if new_sequence < 1 or new_sequence > sibling_filter_interfaces.count() + 1:
            raise ValueError(
                f"New policy sequence {new_sequence} is out of bounds for interface direction {interface_direction.id}."
            )

        for related_filter_interface in sibling_filter_interfaces.filter(policy_sequence__gte=new_sequence):
            related_filter_interface.policy_sequence += 1
            related_filter_interface.save()

        filter_interface.policy_sequence = new_sequence
        filter_interface.save()
        return filter_interface

    if not matching_filter_interfaces.exists():
        if new_sequence != 1:
            raise ValueError(
                f"There are no filters attached to interface direction {interface_direction.id}, so the only valid sequence is 1."
            )
        filter_interface.policy_sequence = new_sequence
        filter_interface.save()
        return filter_interface

    if new_sequence < 1 or new_sequence > matching_filter_interfaces.count() + 1:
        raise ValueError(
            f"New policy sequence {new_sequence} is out of bounds for interface direction {interface_direction.id}."
        )

    if filter_interface.policy_sequence == new_sequence:
        return filter_interface

    if filter_interface.policy_sequence < new_sequence:
        for related_filter_interface in matching_filter_interfaces.filter(
            policy_sequence__gt=filter_interface.policy_sequence,
            policy_sequence__lte=new_sequence,
        ):
            related_filter_interface.policy_sequence -= 1
            related_filter_interface.save()
    else:
        for related_filter_interface in matching_filter_interfaces.filter(
            policy_sequence__lt=filter_interface.policy_sequence,
            policy_sequence__gte=new_sequence,
        ):
            related_filter_interface.policy_sequence += 1
            related_filter_interface.save()

    filter_interface.policy_sequence = new_sequence
    filter_interface.save()
    return filter_interface


@transaction.atomic
def update_filter_interface(
    *,
    actor,
    tenant_id,
    filter_interface_id,
    direction=None,
    policy_sequence=None,
    enable=None,
):
    require_write_tenant(actor, tenant_id)

    filter_interface = (
        FilterInterface.objects.select_related("filter", "interface_direction__interface__device")
        .filter(
            id=filter_interface_id,
            filter__tenant_id__in=_editable_tenant_ids(actor, tenant_id),
        )
        .first()
    )
    if filter_interface is None:
        raise PermissionDenied(f"Filter interface {filter_interface_id} does not belong to tenant {tenant_id}.")

    if direction is not None:
        filter_interface.direction = direction
    if enable is not None:
        filter_interface.enable = enable
    filter_interface.save()

    if policy_sequence is not None:
        return update_filter_interface_sequence(
            actor=actor,
            tenant_id=tenant_id,
            filter_interface=filter_interface,
            new_sequence=policy_sequence,
        )

    return filter_interface


@transaction.atomic
def _reorder_rules_after_removal(rule, old_filter_id, old_sequence):
    for related_rule in Rule.objects.filter(filter_id=old_filter_id, rule_sequence__gt=old_sequence).order_by(
        "rule_sequence"
    ):
        related_rule.rule_sequence -= 1
        related_rule.save()


@transaction.atomic
def _insert_rule_into_filter(rule, target_filter, new_sequence):
    target_rules = Rule.objects.filter(filter=target_filter).order_by("rule_sequence")
    if new_sequence < 1 or new_sequence > target_rules.count() + 1:
        raise ValueError(f"New sequence {new_sequence} is out of bounds for filter with id={target_filter.id}.")

    for related_rule in target_rules.filter(rule_sequence__gte=new_sequence):
        related_rule.rule_sequence += 1
        related_rule.save()

    rule.rule_sequence = new_sequence
    rule.filter = target_filter
    rule.save()
    return rule


@transaction.atomic
def update_rule_sequence(*, actor, tenant_id, rule, new_sequence):
    require_write_tenant(actor, tenant_id)

    scoped_rule = (
        Rule.objects.select_related("filter")
        .filter(
            id=rule.id,
            tenant_id__in=_editable_tenant_ids(actor, tenant_id),
        )
        .first()
    )
    if scoped_rule is None:
        raise PermissionDenied(f"Rule with id={rule.id} does not belong to tenant {tenant_id}.")

    filter_obj = scoped_rule.filter
    if filter_obj is None:
        raise ValueError(f"Rule with id={scoped_rule.id} does not belong to any filter.")

    rules_in_filter = Rule.objects.filter(filter=filter_obj).order_by("rule_sequence")

    if not rules_in_filter.exists():
        if new_sequence != 1:
            raise ValueError(
                f"There are no rules in filter with id={filter_obj.id}, so the only valid sequence is 1."
            )
        scoped_rule.rule_sequence = new_sequence
        scoped_rule.save()
        return scoped_rule

    if new_sequence < 1 or new_sequence > rules_in_filter.count() + 1:
        raise ValueError(f"New sequence {new_sequence} is out of bounds for filter with id={filter_obj.id}.")

    if scoped_rule.rule_sequence == 0:
        for related_rule in rules_in_filter.filter(rule_sequence__gte=new_sequence):
            related_rule.rule_sequence += 1
            related_rule.save()

        scoped_rule.rule_sequence = new_sequence
        scoped_rule.save()
        return scoped_rule

    if scoped_rule.rule_sequence == new_sequence:
        return scoped_rule

    if scoped_rule.rule_sequence < new_sequence:
        for related_rule in rules_in_filter.filter(
            rule_sequence__gt=scoped_rule.rule_sequence,
            rule_sequence__lte=new_sequence,
        ):
            related_rule.rule_sequence -= 1
            related_rule.save()
    else:
        for related_rule in rules_in_filter.filter(
            rule_sequence__lt=scoped_rule.rule_sequence,
            rule_sequence__gte=new_sequence,
        ):
            related_rule.rule_sequence += 1
            related_rule.save()

    scoped_rule.rule_sequence = new_sequence
    scoped_rule.save()
    return scoped_rule


@transaction.atomic
def update_rule(
    *,
    actor,
    tenant_id,
    rule_id,
    filter=None,
    name=None,
    description=None,
    action=None,
    enable=None,
    rule_sequence=None,
    log_type=None,
    hit_count=None,
    changed_by=None,
):
    require_write_tenant(actor, tenant_id)

    rule = Rule.objects.filter(id=rule_id, tenant_id__in=_editable_tenant_ids(actor, tenant_id)).first()
    if rule is None:
        raise PermissionDenied(f"Rule with ID {rule_id} does not exist in tenant {tenant_id}.")

    original_filter_id = rule.filter_id
    original_rule_sequence = rule.rule_sequence
    target_filter = None

    if filter is not None:
        validated_filter = Filter.objects.filter(
            id=filter.id,
            tenant_id__in=_editable_tenant_ids(actor, tenant_id),
        ).first()
        if validated_filter is None:
            raise PermissionDenied(f"Filter with ID {filter.id} does not exist in tenant {tenant_id}.")
        target_filter = validated_filter
        rule.filter = validated_filter

    if name is not None:
        rule.name = name
    if description is not None:
        rule.description = description
    if action is not None:
        rule.action = action
    if enable is not None:
        rule.enable = enable
    if rule_sequence is not None:
        rule.rule_sequence = rule_sequence

    if filter is not None and rule_sequence is not None and original_filter_id != target_filter.id:
        _reorder_rules_after_removal(rule, original_filter_id, original_rule_sequence)
        return _insert_rule_into_filter(rule, target_filter, rule_sequence)

    if rule_sequence is not None:
        update_rule_sequence(actor=actor, tenant_id=tenant_id, rule=rule, new_sequence=rule_sequence)
    if log_type is not None:
        rule.log_type = log_type
    if hit_count is not None:
        rule.hit_count = hit_count
    if changed_by is not None:
        rule.changed_by = changed_by

    rule.save()
    return rule
