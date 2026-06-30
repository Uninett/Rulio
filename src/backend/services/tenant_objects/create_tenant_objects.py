from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.models import User

from backend.objects.tenant_objects.interface import Interface
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


def create_device(*, actor: User, tenant_id: int, name: str, platform: str, description: str, type: str) -> object:

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


def create_device_group(*, actor: User, tenant_id: int, name: str, description: str) -> object:
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


def create_interface(
    *, actor: User, tenant_id: int, name: str, description: str, device_id: int, type: str, VRF: str = None
) -> object:
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
    return interface
