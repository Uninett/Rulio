from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from django.core.exceptions import ValidationError as DjangoValidationError

from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.management.tenant import Tenant
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.utils.logger import set_up_logger
from django.db import transaction


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


def add_service_to_group(
    request: object, service_group_id: int, service_id: int
) -> ServiceGroup:
    service_group = ServiceGroup.objects.get(id=service_group_id)
    service = Service.objects.get(id=service_id)
    service_group.services.add(service)
    logger.info(f"Added {service} to {service_group}")
    return service_group


def add_services_to_group(service_group_id: int, service_ids: list[int]) -> dict:
    service_group = ServiceGroup.objects.get(id=service_group_id)

    requested_ids = set(service_ids)

    existing_services = Service.objects.filter(id__in=requested_ids)
    found_ids = {service.id for service in existing_services}
    not_found_ids = requested_ids - found_ids

    already_present_ids = set(
        ServiceGroupMember.objects.filter(
            group=service_group,
            service_id__in=found_ids,
        ).values_list("service_id", flat=True)
    )

    new_services = [
        service
        for service in existing_services
        if service.id not in already_present_ids
    ]

    with transaction.atomic():
        ServiceGroupMember.objects.bulk_create(
            [
                ServiceGroupMember(group=service_group, service=service)
                for service in new_services
            ]
        )

    added_ids = [service.id for service in new_services]

    logger.info(
        f"Group {service_group.id}: added={added_ids}, "
        f"already_present={list(already_present_ids)}, "
        f"not_found={list(not_found_ids)}"
    )

    return {
        "service_group_id": service_group.id,
        "added_service_ids": sorted(added_ids),
        "already_present_service_ids": sorted(already_present_ids),
        "not_found_service_ids": sorted(not_found_ids),
    }

def add_addresses_to_group(address_group_id: int, address_ids: list[int]) -> dict:
    address_group = AddressGroup.objects.get(id=address_group_id)

    request_ids = set(address_ids)

    existing_addresses = Address.objects.filter(id_in=request_ids)
    found_ids = {address.id for address in existing_addresses}
    not_found_ids = request_ids - found_ids
    already_present_ids = set(AddressGroupMember.objects.filter(group=address_group,address_id__in=found_ids,).values_list("address_id",flat=True))

    new_addresses=[
        address 
        for address in existing_addresses
        if address.id not in already_present_ids
    ]

    with transaction.atomic():
        AddressGroupMember.objects.bulk_create(
            [
                AddressGroupMember(group=address_group, address=address)
                for address in new_addresses
            ]
        )
    added_ids = [address.id for address in new_addresses]

    logger.info(
        f"Group {address_group.id}: added={added_ids}, "
        f"already_present={list(already_present_ids)}, "
        f"not_found={list(not_found_ids)}"
    )

    return {
        "address_group_id": address_group.id,
        "added_address_ids": sorted(added_ids),
        "already_present_address_ids": sorted(already_present_ids),
        "not_found_address_ids": sorted(not_found_ids),
    }


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
    )
    try:
        address_group.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Address Group validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    address_group.save()
    logger.info(f"Created {address_group} for tenant={address_group.tenant_id}")
    return address_group


def create_tenant(request: object, name: str) -> Tenant:
    tenant = Tenant.objects.create(tenant_name=name)
    logger.info(f"Tenant created: {tenant}")
    return tenant


def create_tenant_user_member(
    request: object, tenant_id: int, user_id: int, role: str
) -> TenantUserMember:
    tenant_user = TenantUserMember.objects.create(tenant_id=tenant_id, user_id=user_id)
    logger.info(f"TenantUserMember created: {tenant_user}")
    return tenant_user


def create_address_group(request: object, name: str, description: str, tenant_id: int):
    address_group = AddressGroup.objects.create(name=name, description=description, tenant_id=tenant_id)
    logger.info(f"Address Group created with name={name} and description={description}")
    return address_group


def add_address_to_group(
    request: object, address_group_id: int, address_id: int
) -> AddressGroup:
    address_group = AddressGroup.objects.get(id=address_group_id)
    address = Address.objects.get(id=address_id)
    address_group.addresses.add(address)
    logger.info(f"Added {address} to {address_group}")
    return address_group
