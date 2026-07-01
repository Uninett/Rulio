from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.core.exceptions import PermissionDenied


from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.attributes.service import Service
from backend.services.helper_user_tenant import require_read_tenant
from backend.utils.logger import set_up_logger


# Setup logger
logger = set_up_logger(__name__)



def get_all_service_groups_from_tenant(actor: User, tenant_id: int) -> QuerySet[ServiceGroup]:
    require_read_tenant(actor, tenant_id)
    requested_service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)
    return requested_service_groups

def get_service_groups_and_services_from_tenant(actor: User, tenant_id: int, include_global_tenant=True, get="all") -> list[dict] | tuple[QuerySet[Service], QuerySet[ServiceGroup]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        service_groups = ServiceGroup.objects.filter(tenant_id__in=[tenant_id, 1])
    else:
        service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id)
    if get == "objects":
        services = Service.objects.filter(tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id])
        return services, service_groups
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
        group__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
        service__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
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

def get_all_services_and_groups_with_tags_from_tenant(actor: User, tenant_id: int, include_global_tenant=True) -> tuple[list[dict], QuerySet[Service], QuerySet[ServiceGroup]]:
    require_read_tenant(actor, tenant_id)
    if include_global_tenant:
        service_groups = ServiceGroup.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
        services = Service.objects.filter(tenant_id__in=[tenant_id, 1]).prefetch_related("tag_objects__tag")
    else:
        service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")
        services = Service.objects.filter(tenant_id=tenant_id).prefetch_related("tag_objects__tag")

    memberships = ServiceGroupMember.objects.filter(
        group__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
        service__tenant_id__in=[tenant_id, 1] if include_global_tenant else [tenant_id],
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

    return result, services, service_groups

def get_all_services_from_tenant(actor: User, tenant_id: int, get="objects") -> list[Service]:
    require_read_tenant(actor, tenant_id)
    requested_services = Service.objects.filter(tenant_id=tenant_id)
    if get == "objects":
        return requested_services
    elif get == "ids":
        return [{"service_id": service.id} for service in requested_services]
    elif get == "names":
        return [{"service_name": service.name} for service in requested_services]

def get_all_services_from_tenant_by_names(actor: User, tenant_id: int, names: list[str]) -> QuerySet[Service]:
    require_read_tenant(actor, tenant_id)
    requested_services = Service.objects.filter(tenant_id=tenant_id, name__in=names)
    return requested_services

def get_service_group_members(actor: User, tenant_id: int, service_group_id: int) -> QuerySet[Service]:
    require_read_tenant(actor, tenant_id)
    if not ServiceGroup.objects.filter(id=service_group_id, tenant_id=tenant_id).exists():
        raise PermissionDenied(f"Service group with ID {service_group_id} does not exist in tenant {tenant_id}.")
    return Service.objects.filter(servicegroupmember__group_id=service_group_id)

def get_all_services_with_certain_tags_from_tenant(actor: User, tenant_id: int, tag_names: list[str]) -> QuerySet[Service]:
    require_read_tenant(actor, tenant_id)
    requested_services = Service.objects.filter(tenant_id=tenant_id, tag_objects__tag__name__in=tag_names).distinct()
    return requested_services

def get_all_service_groups_with_certain_tags_from_tenant(actor: User, tenant_id: int, tag_names: list[str]) -> QuerySet[ServiceGroup]:
    require_read_tenant(actor, tenant_id)
    requested_service_groups = ServiceGroup.objects.filter(tenant_id=tenant_id, tag_objects__tag__name__in=tag_names).distinct()
    return requested_service_groups