from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.utils.logger import set_up_logger


# Setup logger
logger = set_up_logger(__name__)


def get_all_service_groups_from_tenant(tenant_id: int) -> list[ServiceGroup]:
    requested_service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)
    return requested_service_groups


def get_service_groups_with_services_from_tenant(tenant_id: int, get="all") -> list[dict]:
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
    elif get == "names":
        return [{"service_group_name": group["service_group_name"]} for group in result]


def get_address_groups_with_addresses_from_tenant(tenant_id: int, get="all") -> list[dict]:
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

    if get == "all":
        return result
    elif get == "ids":
        return [{"address_group_id": group["address_group_id"]} for group in result]
    elif get == "names":
        return [{"address_group_name": group["address_group_name"]} for group in result]


def get_all_address_groups_from_tenant(tenant_id: int) -> list[AddressGroup]:
    requested_address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)
    return requested_address_groups


def get_all_services_from_tenant(tenant_id: int, get="all") -> list[Service]:
    requested_services = Service.objects.filter(tenant_id=tenant_id)
    if get == "all":
        return requested_services
    elif get == "ids":
        return [{"service_id": service.id} for service in requested_services]
    elif get == "names":
        return [{"service_name": service.name} for service in requested_services]


def get_all_addresses_from_tenant(tenant_id: int, get="all") -> list[Address]:
    requested_addresses = Address.objects.filter(tenant_id=tenant_id)
    if get == "all":
        return requested_addresses
    elif get == "ids":
        return [{"address_id": address.id} for address in requested_addresses]
    elif get == "names":
        return [{"address_name": address.name} for address in requested_addresses]
    

def get_address_group_members(request: object, address_group_id: int) -> list[Address]:
    return Address.objects.filter(addressgroupmember__group_id=address_group_id) 
    #return AddressGroupMember.objects.filter(group_id=address_group_id)

def get_service_group_members(request: object, service_group_id: int) -> list[Address]:
    return Service.objects.filter(servicegroupmember__group_id=service_group_id)
    #return ServiceGroupMember.objects.filter(group_id=service_group_id)
