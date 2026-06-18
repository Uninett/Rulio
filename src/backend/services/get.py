from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from django.core.exceptions import ValidationError as DjangoValidationError

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.management.tenant import Tenant
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.utils.logger import set_up_logger


# Setup logger
logger = set_up_logger(__name__)


def get_all_service_groups_from_tenant(tenant_id: int) -> list[ServiceGroup]:
    requested_service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)
    return requested_service_groups


def get_service_groups_with_services_from_tenant(
    tenant_id: int, get="all"
) -> list[dict]:
    service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)

    result = []
    group_map = {}

    for group in service_groups:
        group_dict = {
            "service_group_id": group.id,
            "service_group_name": group.name,
            "services": [],
        }
        result.append(group_dict)
        group_map[group.id] = group_dict

    memberships = ServiceGroupMember.objects.filter(
        group__tenant_id=tenant_id,
        service__tenant_id=tenant_id,
    ).select_related("group", "service")

    for membership in memberships:
        group_id = membership.group.id

        if group_id in group_map:
            group_map[group_id]["services"].append(
                {
                    "service_id": membership.service.id,
                    "service_name": membership.service.name,
                    "description": membership.service.description,
                    "protocol": membership.service.protocol,
                    "port_start": membership.service.port_start,
                    "port_end": membership.service.port_end,
                }
            )
    if get == "all":
        return result
    elif get == "ids":
        return [{"service_group_id": group["service_group_id"]} for group in result]


def get_address_groups_with_addresses_from_tenant(tenant_id: int) -> list[dict]:
    address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)

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
        group_id__tenant_id=tenant_id,
        address_id__tenant_id=tenant_id,
    ).select_related("group_id", "address_id")

    for membership in memberships:
        group_id = membership.group_id.id

        if group_id in group_map:
            group_map[group_id]["addresses"].append(
                {
                    "address_id": membership.address_id.id,
                    "address_name": membership.address_id.name,
                    "ipv4_type": membership.address_id.ipv4_type,
                    "ipv6_type": membership.address_id.ipv6_type,
                    "ipv4Network": membership.address_id.ipv4Network,
                    "ipv6Network": membership.address_id.ipv6Network,
                    "ipv4Address_start": membership.address_id.ipv4Address_start,
                    "ipv4Address_end": membership.address_id.ipv4Address_end,
                    "ipv6Address_start": membership.address_id.ipv6Address_start,
                    "ipv6Address_end": membership.address_id.ipv6Address_end,
                }
            )

    return result


def get_all_address_groups_from_tenant(tenant_id: int) -> list[AddressGroup]:
    requested_address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)
    return requested_address_groups
