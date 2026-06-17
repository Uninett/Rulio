from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from django.core.exceptions import ValidationError as DjangoValidationError

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.management.tenant import Tenant
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.utils.logger import set_up_logger


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
    ipv4_type: str | None,
    ipv6_type: str | None,
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
    ipv4_type: str | None,
    ipv6_type: str | None,
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


def create_tenant(request: object, name: str):
    tenant = Tenant.objects.create(tenant_name=name)
    logger.info(f"Tenant created: {tenant}")
    return tenant


def create_tenant_user_member(request: object, tenant_id: int, user_id: int, role: str):
    tenant_user = TenantUserMember.objects.create(tenant_id=tenant_id, user_id=user_id)
    logger.info(f"TenantUserMember created: {tenant_user}")
    return tenant_user


def create_address_group(request: object, name: str, description: str, tenant_id: int):
    address_group = AddressGroup.objects.create(
        name=name, description=description, tenant_id=tenant_id
    )
    logger.info(f"Address Group created with name={name} and description={description}")
    return address_group

def add_address_to_group(request: object, address_group_id: int, address_id: int):
    address_group = AddressGroup.objects.get(id=address_group_id)
    address = Address.objects.get(id=address_id)
    address_group.addresses.add(address)
    logger.info(f"Added {address} to {address_group}")
    return address_group