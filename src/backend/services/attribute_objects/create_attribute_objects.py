from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.models import User

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.tag import Tag
from backend.services.helper_user_tenant import require_write_tenant
from backend.utils.logger import set_up_logger
from backend.services.get import get_object_by_type_and_id
from backend.services.membership import (
    add_addresses_to_group,
    add_services_to_group,
)


logger = set_up_logger(__name__)


def create_address(
    *,
    actor: User,
    tenant_id: int,
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

    require_write_tenant(actor, tenant_id)

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


def create_and_add_address_to_groups(
    *,
    actor: User,
    tenant_id: int,
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
    group_ids: list[int] | None = None,
) -> Address:

    require_write_tenant(actor, tenant_id)

    address = create_address(
        actor=actor,
        tenant_id=tenant_id,
        name=name,
        description=description,
        addr_type=addr_type,
        ipv4_type=ipv4_type,
        ipv6_type=ipv6_type,
        ipv4Network=ipv4Network,
        ipv6Network=ipv6Network,
        ipv4Address_start=ipv4Address_start,
        ipv4Address_end=ipv4Address_end,
        ipv6Address_start=ipv6Address_start,
        ipv6Address_end=ipv6Address_end,
    )

    if group_ids:
        AddressGroupMember.objects.bulk_create(
            [AddressGroupMember(address_id=address.id, group_id=group_id) for group_id in group_ids]
        )
        logger.info(f"Added {address} to groups with IDs {group_ids}")

    return address


def get_or_create_address(
    *,
    actor: User,
    tenant_id: int,
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

    require_write_tenant(actor, tenant_id)

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
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    protocol: str,
    port_start: int | None = None,
    port_end: int | None = None,
) -> Service:

    require_write_tenant(actor, tenant_id)

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


def create_and_add_service_to_groups(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    protocol: str,
    port_start: int | None = None,
    port_end: int | None = None,
    group_ids: list[int] | None = None,
) -> Service:

    require_write_tenant(actor, tenant_id)

    service = create_service(
        actor=actor,
        tenant_id=tenant_id,
        name=name,
        description=description,
        protocol=protocol,
        port_start=port_start,
        port_end=port_end,
    )

    if group_ids:
        ServiceGroupMember.objects.bulk_create(
            [ServiceGroupMember(service_id=service.id, group_id=group_id) for group_id in group_ids]
        )
        logger.info(f"Added {service} to groups with IDs {group_ids}")

    return service


def get_or_create_service(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    protocol: str,
    port_start: int | None = None,
    port_end: int | None = None,
) -> tuple[Service, int, bool]:

    require_write_tenant(actor, tenant_id)

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
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
) -> ServiceGroup:

    require_write_tenant(actor, tenant_id)

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


def create_service_group_and_add_services(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    members: list[int] | None = None,
) -> ServiceGroup:

    require_write_tenant(actor, tenant_id)

    service_group = create_service_group(
        actor=actor,
        tenant_id=tenant_id,
        name=name,
        description=description,
    )

    if members:
        add_services_to_group(actor=actor, tenant_id=tenant_id, service_group_id=service_group.id, service_ids=members)
        logger.info(f"Added members to {service_group}: {members}")

    return service_group


def get_or_create_service_group(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    members: list[int] | None = None,
) -> tuple[ServiceGroup, int, bool]:

    require_write_tenant(actor, tenant_id)

    service_group, created = ServiceGroup.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    if created:
        logger.info(f"Created {service_group} for tenant={service_group.tenant_id}")
        if members:
            add_services_to_group(
                actor=actor, tenant_id=tenant_id, service_group_id=service_group.id, service_ids=members
            )
            logger.info(f"Added members to {service_group}: {members}")
    else:
        logger.warning(f"Service Group already exists: {service_group} for tenant={service_group.tenant_id}")
        if members:
            add_services_to_group(
                actor=actor, tenant_id=tenant_id, service_group_id=service_group.id, service_ids=members
            )
            logger.info(f"Added members to existing {service_group}: {members}")
    return service_group, service_group.id, created


def create_address_group(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
) -> AddressGroup:

    require_write_tenant(actor, tenant_id)

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


def create_address_group_and_add_addresses(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    members: list[int] | None = None,
) -> AddressGroup:

    require_write_tenant(actor, tenant_id)

    address_group = create_address_group(
        actor=actor,
        tenant_id=tenant_id,
        name=name,
        description=description,
    )

    if members:
        add_addresses_to_group(actor=actor, tenant_id=tenant_id, address_group_id=address_group.id, address_ids=members)
        logger.info(f"Added members to {address_group}: {members}")

    return address_group


def get_or_create_address_group(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    members: list[int] | None = None,
) -> tuple[AddressGroup, int, bool]:

    require_write_tenant(actor, tenant_id)

    address_group, created = AddressGroup.objects.get_or_create(
        name=name,
        description=description,
        tenant_id=tenant_id,
        addr_type="Group",
    )
    if created:
        logger.info(f"Created {address_group} for tenant={address_group.tenant_id}")
        if members:
            add_addresses_to_group(
                actor=actor, tenant_id=tenant_id, address_group_id=address_group.id, address_ids=members
            )
            logger.info(f"Added members to {address_group}: {members}")
    else:
        logger.warning(f"Address Group already exists: {address_group} for tenant={address_group.tenant_id}")
        if members:
            add_addresses_to_group(
                actor=actor, tenant_id=tenant_id, address_group_id=address_group.id, address_ids=members
            )
            logger.info(f"Added members to existing {address_group}: {members}")

    return address_group, address_group.id, created


def create_tag(*, actor: User, tenant_id: int, name: str, description: str) -> Tag:

    require_write_tenant(actor, tenant_id)

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
    *, actor: User, tenant_id: int, tag_name: str, tag_description: str, object_type: str, object_id: int
) -> Tag:

    require_write_tenant(actor, tenant_id)

    tag = create_tag(actor=actor, tenant_id=tenant_id, name=tag_name, description=tag_description)
    obj = get_object_by_type_and_id(object_type, object_id)
    if isinstance(obj, TaggableMixin):
        obj.add_tag(tag)
        logger.info(f"Added {tag} to {obj}")
    else:
        logger.warning(f"Object {obj} is not taggable. Created tag {tag} but did not add it to the object.")
    return tag
