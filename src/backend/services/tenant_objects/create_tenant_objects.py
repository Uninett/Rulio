from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.models import User

from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup

from backend.services.helper_user_tenant import require_superadmin, require_write_tenant
from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def create_tenant(actor: User, name: str):
    require_superadmin(actor)
    tenant = Tenant.objects.create(tenant_name=name)
    logger.info(f"Tenant created: {tenant}")
    return tenant


def create_device(*, actor: User, tenant_id: int, name: str, platform: str, description: str, type: str) -> Device:

    require_write_tenant(actor, tenant_id)

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


def get_or_create_device(
    *, actor: User, tenant_id: int, name: str, platform: str, description: str, type: str
) -> Device:
    require_write_tenant(actor, tenant_id)

    device, created = Device.objects.get_or_create(
        name=name,
        platform=platform,
        type=type,
        description=description,
        tenant_id=tenant_id,
    )
    if created:
        logger.info(f"Created {device} for tenant={device.tenant_id}")
    else:
        logger.info(f"Retrieved existing {device} for tenant={device.tenant_id}")
    return device


def create_device_group(*, actor: User, tenant_id: int, name: str, description: str) -> DeviceGroup:
    require_write_tenant(actor, tenant_id)

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


def get_or_create_device_group(*, actor: User, tenant_id: int, name: str, description: str) -> DeviceGroup:
    require_write_tenant(actor, tenant_id)

    device_group, created = DeviceGroup.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    if created:
        logger.info(f"Created {device_group} for tenant={device_group.tenant_id}")
    else:
        logger.info(f"Retrieved existing {device_group} for tenant={device_group.tenant_id}")
    return device_group


def create_interface(
    *, actor: User, tenant_id: int, name: str, description: str, device_id: int, type: str, VRF: str = None
) -> Interface:
    require_write_tenant(actor, tenant_id)
    # Check if the device exists and belongs to the tenant
    try:
        Device.objects.get(id=device_id, tenant_id=tenant_id)
    except Device.DoesNotExist:
        raise ValueError(f"Device with id={device_id} does not exist in tenant={tenant_id}.")

    interface = Interface(
        name=name,
        description=description,
        device_id=device_id,
        type=type,
        VRF=VRF,
    )
    try:
        interface.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Interface validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    interface.save()
    logger.info(f"Created {interface} for device={interface.device_id}")
    interface_direction_in = InterfaceDirection(interface=interface, direction="in")
    interface_direction_out = InterfaceDirection(interface=interface, direction="out")
    interface_direction_in.save()
    interface_direction_out.save()
    try:
        interface_direction_in.full_clean()
        interface_direction_out.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"InterfaceDirection validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e
    logger.info(f"Created InterfaceDirection for {interface} with directions 'in' and 'out'")
    return interface


def get_or_create_interface(
    *, actor: User, tenant_id: int, name: str, description: str, device_id: int, type: str, VRF: str = None
) -> tuple[Interface, bool, InterfaceDirection, bool, InterfaceDirection, bool]:
    require_write_tenant(actor, tenant_id)
    # Check if the device exists and belongs to the tenant
    try:
        Device.objects.get(id=device_id, tenant_id=tenant_id)
    except Device.DoesNotExist:
        raise ValueError(f"Device with id={device_id} does not exist in tenant={tenant_id}.")

    interface, created = Interface.objects.get_or_create(
        name=name,
        description=description,
        device_id=device_id,
        type=type,
        VRF=VRF,
    )
    if created:
        logger.info(f"Created {interface} for device={interface.device_id}")
    else:
        logger.info(f"Retrieved existing {interface} for device={interface.device_id}")
    interface_direction_in, created_in = InterfaceDirection.objects.get_or_create(interface=interface, direction="in")
    interface_direction_out, created_out = InterfaceDirection.objects.get_or_create(
        interface=interface, direction="out"
    )
    if created_in:
        logger.info(f"Created InterfaceDirection for {interface} with direction 'in'")
    if created_out:
        logger.info(f"Created InterfaceDirection for {interface} with direction 'out'")
    return interface, created, interface_direction_in, created_in, interface_direction_out, created_out
