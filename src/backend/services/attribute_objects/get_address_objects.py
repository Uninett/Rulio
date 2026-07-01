from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.core.exceptions import PermissionDenied

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember


from backend.services.helper_user_tenant import require_read_tenant
from backend.utils.logger import set_up_logger


# Setup logger
logger = set_up_logger(__name__)


def get_address_groups_and_addresses_from_tenant(
    actor: User, tenant_id: int, include_global_tenant=True, get="all"
) -> list[dict] | tuple[QuerySet[Address], QuerySet[AddressGroup]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        address_groups = AddressGroup.objects.filter(tenant_id__in=[tenant_id, 1])
    else:
        address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)

    if get == "objects":
        addresses = Address.objects.filter(tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id])
        return addresses, address_groups

    result = []
    group_map = {}

    for group in address_groups:
        group_dict = {
            "address_group_id": group.id,
            "address_group_name": group.name,
            "addresses": [],
        }
        result.append(group_dict)
        group_map[group.id] = group_dict

    memberships = AddressGroupMember.objects.filter(
        group__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
        address__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
    ).select_related("group", "address")

    for membership in memberships:
        group_id = membership.group.id

        if group_id in group_map:
            group_map[group_id]["addresses"].append(
                {
                    "address_id": membership.address.id,
                    "address_name": membership.address.name,
                    "addr_type": membership.address.addr_type,
                    "ipv4_type": membership.address.ipv4_type,
                    "ipv6_type": membership.address.ipv6_type,
                    "ipv4Network": membership.address.ipv4Network,
                    "ipv6Network": membership.address.ipv6Network,
                    "ipv4Address_start": membership.address.ipv4Address_start,
                    "ipv4Address_end": membership.address.ipv4Address_end,
                    "ipv6Address_start": membership.address.ipv6Address_start,
                    "ipv6Address_end": membership.address.ipv6Address_end,
                }
            )

    if get == "all":
        return result
    elif get == "ids":
        return [{"address_group_id": group["address_group_id"]} for group in result]
    elif get == "names":
        return [{"address_group_name": group["address_group_name"]} for group in result]
    raise ValueError(f"Invalid value for 'get': {get}. Must be one of 'all', 'ids', or 'names'.")


def get_all_addresss_groups_with_tags_from_tenant(
    actor: User, tenant_id: int, include_global_tenant=True
) -> tuple[list[dict], QuerySet[AddressGroup]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        address_groups = AddressGroup.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
    else:
        address_groups = AddressGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    result = []
    for group in address_groups:
        result.append(
            {
                "address_group_id": group.id,
                "address_group_name": group.name,
                "address_group_description": group.description,
                "address_group_tags": [
                    {
                        "tag_id": tc.tag.id,
                        "tag_name": tc.tag.name,
                        "tag_description": tc.tag.description,
                    }
                    for tc in group.tag_objects.all()
                ],
            }
        )

    return result, address_groups


def get_all_addresses_and_groups_with_tags_from_tenant(
    actor: User, tenant_id: int, include_global_tenant=True
) -> tuple[list[dict], QuerySet[Address], QuerySet[AddressGroup]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        address_groups = AddressGroup.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
        addresses = Address.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
    else:
        address_groups = AddressGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")
        addresses = Address.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    memberships = AddressGroupMember.objects.filter(
        group__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
        address__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
    ).select_related("group", "address")

    addresses_by_group = {}
    groups_by_address = {}

    for membership in memberships:
        group = membership.group
        address = membership.address

        addresses_by_group.setdefault(group.id, []).append(
            {
                "id": address.id,
                "name": address.name,
            }
        )

        groups_by_address.setdefault(address.id, []).append(
            {
                "id": group.id,
                "name": group.name,
            }
        )

    result = []

    for group in address_groups:
        result.append(
            {
                "type": "AddressGroup",
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in group.tag_objects.all()
                ],
                "addresses": addresses_by_group.get(group.id, []),
            }
        )

    for address in addresses:
        result.append(
            {
                "type": "Address",
                "id": address.id,
                "name": address.name,
                "description": address.description,
                "addr_type": address.addr_type,
                "ipv4_type": address.ipv4_type,
                "ipv6_type": address.ipv6_type,
                "ipv4Network": address.ipv4Network,
                "ipv6Network": address.ipv6Network,
                "ipv4Address_start": address.ipv4Address_start,
                "ipv4Address_end": address.ipv4Address_end,
                "ipv6Address_start": address.ipv6Address_start,
                "ipv6Address_end": address.ipv6Address_end,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in address.tag_objects.all()
                ],
                "address_groups": groups_by_address.get(address.id, []),
            }
        )

    return result, addresses, address_groups


def get_all_address_groups_from_tenant(actor: User, tenant_id: int) -> QuerySet[AddressGroup]:
    require_read_tenant(actor, tenant_id)
    requested_address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)
    return requested_address_groups


def get_all_addresses_from_tenant(actor: User, tenant_id: int, get="objects") -> list[dict] | QuerySet[Address]:
    require_read_tenant(actor, tenant_id)
    requested_addresses = Address.objects.filter(tenant_id=tenant_id)
    if get == "objects":
        return requested_addresses
    elif get == "ids":
        return [{"address_id": address.id} for address in requested_addresses]
    elif get == "names":
        return [{"address_name": address.name} for address in requested_addresses]


def get_all_addresses_from_tenant_by_names(actor: User, tenant_id: int, names: list[str]) -> QuerySet[Address]:
    require_read_tenant(actor, tenant_id)
    requested_addresses = Address.objects.filter(tenant_id=tenant_id, name__in=names)
    return requested_addresses


def get_address_group_members(actor: User, tenant_id: int, address_group_id: int) -> QuerySet[Address]:
    require_read_tenant(actor, tenant_id)
    if not AddressGroup.objects.filter(id=address_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Address group with ID {address_group_id} does not exist in tenant {tenant_id}.")
    return Address.objects.filter(addressgroupmember__group_id=address_group_id)


def get_all_addresses_with_certain_tags_from_tenant(
    actor: User, tenant_id: int, tag_names: list[str]
) -> QuerySet[Address]:
    require_read_tenant(actor, tenant_id)
    requested_addresses = Address.objects.filter(tenant_id=tenant_id, tag_objects__tag__name__in=tag_names).distinct()
    return requested_addresses


def get_all_address_groups_with_certain_tags_from_tenant(
    actor: User, tenant_id: int, tag_names: list[str]
) -> QuerySet[AddressGroup]:
    require_read_tenant(actor, tenant_id)
    requested_address_groups = AddressGroup.objects.filter(
        tenant_id=tenant_id, tag_objects__tag__name__in=tag_names
    ).distinct()
    return requested_address_groups
