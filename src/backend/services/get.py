from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service import Service
from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.management.tenant import Tenant
from backend.utils.logger import set_up_logger


# Setup logger
logger = set_up_logger(__name__)

DJANGO_MODEL_MAPPING = {
    "address": Address,
    "addressgroup": AddressGroup,
    "service": Service,
    "servicegroup": ServiceGroup,
    "rule": Rule,
    "tag": Tag,
    "addressgroupmember": AddressGroupMember,
    "servicegroupmember": ServiceGroupMember,
    "filter": Filter,
}


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


def get_current_tenant(request: object) -> Tenant:
    tenant_id = get_current_tenant_id(request)
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        return tenant
    except Tenant.DoesNotExist:
        logger.warning(f"Tenant with ID {tenant_id} does not exist.")
        raise Exception(f"Tenant with ID {tenant_id} does not exist.")


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
        group__tenant_id=tenant_id,
        address__tenant_id=tenant_id,
    ).select_related("group", "address")

    for membership in memberships:
        group_id = membership.group.id

        if group_id in group_map:
            group_map[group_id]["addresses"].append(
                {
                    "address_id": membership.address.id,
                    "address_name": membership.address.name,
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


def get_all_addresses_and_groups_with_tags(tenant_id: int) -> list[dict]:
    address_groups = AddressGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")
    addresses = Address.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    memberships = AddressGroupMember.objects.filter(
        group__tenant_id=tenant_id,
        address__tenant_id=tenant_id,
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

    return result


def get_all_services_and_groups_with_tags(tenant_id: int) -> list[dict]:
    service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")
    services = Service.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    memberships = ServiceGroupMember.objects.filter(
        group__tenant_id=tenant_id,
        service__tenant_id=tenant_id,
    ).select_related("group", "service")

    services_by_group = {}
    groups_by_service = {}

    for membership in memberships:
        group = membership.group
        service = membership.service

        services_by_group.setdefault(group.id, []).append(
            {
                "id": service.id,
                "name": service.name,
            }
        )

        groups_by_service.setdefault(service.id, []).append(
            {
                "id": group.id,
                "name": group.name,
            }
        )

    result = []

    for group in service_groups:
        result.append(
            {
                "type": "ServiceGroup",
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
                "services": services_by_group.get(group.id, []),
            }
        )

    for service in services:
        result.append(
            {
                "type": "Service",
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "protocol": service.protocol,
                "port_start": service.port_start,
                "port_end": service.port_end,
                "tags": [
                    {
                        "id": tc.tag.id,
                        "name": tc.tag.name,
                        "description": tc.tag.description,
                    }
                    for tc in service.tag_objects.all()
                ],
                "service_groups": groups_by_service.get(service.id, []),
            }
        )

    return result


def get_all_address_groups_from_tenant(tenant_id: int) -> list[AddressGroup]:
    requested_address_groups = AddressGroup.objects.filter(tenant_id=tenant_id)
    return requested_address_groups


def get_all_addresses_from_tenant(tenant_id: int, get="all") -> list:
    requested_addresses = Address.objects.filter(tenant_id=tenant_id)
    if get == "all":
        return requested_addresses
    elif get == "ids":
        return [{"address_id": address.id} for address in requested_addresses]
    elif get == "names":
        return [{"address_name": address.name} for address in requested_addresses]


def get_all_addresses_from_tenant_by_names(tenant_id: int, names: list[str]) -> list[Address]:
    requested_addresses = Address.objects.filter(tenant_id=tenant_id, name__in=names)
    return requested_addresses


def get_address_group_members(request: object, address_group_id: int) -> list[Address]:
    return Address.objects.filter(addressgroupmember__group_id=address_group_id)
    # return AddressGroupMember.objects.filter(group_id=address_group_id)


def get_all_services_from_tenant(tenant_id: int, get="all") -> list[Service]:
    requested_services = Service.objects.filter(tenant_id=tenant_id)
    if get == "all":
        return requested_services
    elif get == "ids":
        return [{"service_id": service.id} for service in requested_services]
    elif get == "names":
        return [{"service_name": service.name} for service in requested_services]


def get_all_services_from_tenant_by_names(tenant_id: int, names: list[str]) -> list[Service]:
    requested_services = Service.objects.filter(tenant_id=tenant_id, name__in=names)
    return requested_services


def get_service_group_members(request: object, service_group_id: int) -> list[Address]:
    return Service.objects.filter(servicegroupmember__group_id=service_group_id)
    # return ServiceGroupMember.objects.filter(group_id=service_group_id)


def get_all_tags_from_object(object_id: int, object_type: str) -> list[Tag]:
    obj = get_object_by_type_and_id(object_type, object_id)
    return list(obj.get_tags())


def get_all_tags_from_tenant(tenant_id: int) -> list[Tag]:
    return Tag.objects.filter(tenant_id=tenant_id)


def get_object_by_type_and_id(object_type: str, object_id: int):
    object_type = object_type.lower()
    model = DJANGO_MODEL_MAPPING.get(object_type)
    if not model:
        raise ValueError(f"Unsupported object type: {object_type}")
    return model.objects.get(id=object_id)


def get_all_rules_from_tenant(tenant_id: int) -> list[Rule]:
    requested_rules = Rule.objects.filter(tenant_id=tenant_id)
    return requested_rules
