


# Create update.py in /services for objects page (first addresses/services, then all other objects later such as devices, filters etc.). Make it possible to update/edit an existing object without creating a new object.

# For object page, these methods are needed. The modal should treat the whole update as one object (i.e. address with address group), so the most important methods are update_address/service_and_groups() and update_address/service_group_and_addresses/services().




from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.services.helper_user_tenant import require_write_tenant


def update_address(*, actor, tenant_id, address_id, name=None, description=None, addr_type=None, ipv4_type=None, ipv6_type=None, ipv4Network=None, ipv6Network=None, ipv4Address_start=None, ipv4Address_end=None, ipv6Address_start=None, ipv6Address_end=None):
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
    address.save()
    return address

def update_service(*, actor, tenant_id, service_id, name=None, description=None, protocol=None, port_start=None, port_end=None, service_type=None):
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

