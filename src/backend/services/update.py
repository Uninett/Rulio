from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_filter import RuleFilter
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.objects.tenant_objects.interface import Interface
from backend.services.helper_user_tenant import require_write_tenant


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
    address = Address.objects.get(id=address_id, tenant_id=tenant_id)
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
    service = Service.objects.get(id=service_id, tenant_id=tenant_id)
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


def update_address_group(*, actor, tenant_id, address_group_id, name=None, description=None, addr_type=None):
    require_write_tenant(actor, tenant_id)
    address_group = AddressGroup.objects.get(id=address_group_id, tenant_id=tenant_id)
    if name is not None:
        address_group.name = name
    if description is not None:
        address_group.description = description
    if addr_type is not None and addr_type.lower() != "group":
        raise ValueError("Address group type must be 'group'.")
    address_group.save()
    return address_group


def update_service_group(*, actor, tenant_id, service_group_id, name=None, description=None, service_type=None):
    require_write_tenant(actor, tenant_id)
    service_group = ServiceGroup.objects.get(id=service_group_id, tenant_id=tenant_id)
    if name is not None:
        service_group.name = name
    if description is not None:
        service_group.description = description
    if service_type is not None and service_type.lower() != "group":
        raise ValueError("Service group type must be 'group'.")
    service_group.save()
    return service_group


def update_device(*, actor, tenant_id, device_id, name=None, description=None, platform=None, type=None):
    require_write_tenant(actor, tenant_id)
    device = Device.objects.get(id=device_id, tenant_id=tenant_id)
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


def update_device_group(*, actor, tenant_id, device_group_id, name=None, description=None):
    require_write_tenant(actor, tenant_id)
    device_group = DeviceGroup.objects.get(id=device_group_id, tenant_id=tenant_id)
    if name is not None:
        device_group.name = name
    if description is not None:
        device_group.description = description
    device_group.save()
    return device_group


def update_tag(*, actor, tenant_id, tag_id, name=None, description=None):
    require_write_tenant(actor, tenant_id)
    tag = Tag.objects.get(id=tag_id, tenant_id=tenant_id)
    if name is not None:
        tag.name = name
    if description is not None:
        tag.description = description
    tag.save()
    return tag


def update_interface(*, actor, tenant_id, interface_id, name=None, description=None, type=None, VRF=None):
    require_write_tenant(actor, tenant_id)
    if Interface.objects.get(id=interface_id).device.tenant_id != tenant_id:
        raise ValueError("Interface does not belong to the specified tenant.")
    interface = Interface.objects.get(id=interface_id)
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


def update_filter(*, actor, tenant_id, filter_id, name=None, description=None):
    require_write_tenant(actor, tenant_id)
    filter = Filter.objects.get(id=filter_id, tenant_id=tenant_id)
    if name is not None:
        filter.name = name
    if description is not None:
        filter.description = description
    filter.save()
    return filter


def update_filter_interface(
    *, actor, tenant_id, filter_interface_id, direction=None, policy_sequence=None, enable=None
):
    require_write_tenant(actor, tenant_id)
    filter_interface = FilterInterface.objects.get(id=filter_interface_id, tenant_id=tenant_id)
    if direction is not None:
        filter_interface.direction = direction
    if policy_sequence is not None:
        filter_interface.policy_sequence = policy_sequence
    if enable is not None:
        filter_interface.enable = enable
    filter_interface.save()
    return filter_interface


def update_rule(
    *,
    actor,
    tenant_id,
    rule_id,
    name=None,
    description=None,
    action=None,
    log_type=None,
    hit_count=None,
    changed_by=None,
    direction=None,
):
    require_write_tenant(actor, tenant_id)
    rule = Rule.objects.get(id=rule_id, tenant_id=tenant_id)
    if name is not None:
        rule.name = name
    if description is not None:
        rule.description = description
    if action is not None:
        rule.action = action
    if log_type is not None:
        rule.log_type = log_type
    if hit_count is not None:
        rule.hit_count = hit_count
    if changed_by is not None:
        rule.changed_by = changed_by
    if direction is not None:
        rule.direction = direction
    rule.save()
    return rule


def update_rule_filter(*, actor, tenant_id, rule_filter_id, rule_sequence=None, enable=None):
    require_write_tenant(actor, tenant_id)
    rule_filter = RuleFilter.objects.get(id=rule_filter_id, tenant_id=tenant_id)
    if rule_sequence is not None:
        rule_filter.rule_sequence = rule_sequence
    if enable is not None:
        rule_filter.enable = enable
    rule_filter.save()
    return rule_filter
