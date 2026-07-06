from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from ninja import NinjaAPI, Status
from ninja.security import django_auth
from django.conf import settings


from backend.objects.attributes.service import Service
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.schemas.address_group import CreateGroupSchema
from backend.schemas.device import CreateDeviceSchema
from backend.schemas.filter import CreateFilterSchema
from backend.schemas.interface import CreateInterfaceSchema
from backend.schemas.tenant_user import CreateTenantUserSchema
from backend.services.authentication import require_read_tenantd, require_superadmind, require_write_tenantd
from backend.services.debugging.add_test_data import create_interfaces_devices_devicegroups_tags
from backend.services.delete import (
    clear_all_tags_from_object,
    delete_device,
    delete_filter,
    delete_interface,
    delete_tag_from_tenant,
    remove_tag_from_object,
    delete_rule,
    delete_tenant,
)
from backend.services.generate_config import generate_multi_policy_config
from backend.services.attribute_objects.get_address_objects import (
    get_address_groups_and_addresses_from_tenant,
    get_all_addresses_and_groups_with_tags_from_tenant,
)
from backend.services.attribute_objects.get_service_objects import (
    get_service_groups_and_services_from_tenant,
    get_all_services_and_groups_with_tags_from_tenant,
)
from backend.services.get import (
    get_all_devices_from_tenant,
    get_all_filters_from_interface,
    get_all_filters_from_tenant,
    get_all_interfaces_from_device,
    get_all_tags_from_object,
    get_all_tags_from_tenant,
    get_all_rules_from_tenant,
    get_all_rules_with_objects_from_tenant,
)
from backend.services.attribute_objects.create_attribute_objects import (
    create_address,
    create_address_group_and_add_addresses,
    create_service,
    create_service_group_and_add_services,
    create_and_add_address_to_groups,
    create_and_add_service_to_groups,
    create_address_group,
    create_service_group,
    create_tag,
    create_and_add_tag_to_object,
)

from backend.services.tenant_objects.create_tenant_objects import (
    create_device,
    create_device_group,
    create_interface,
    create_tenant,
)

from backend.services.filter_objects.create_filter_objects import create_filter, create_rule

from backend.services.create import (
    create_policies_for_interface,
    create_tenant_user_member,
)
from backend.schemas.address import CreateAddressSchema
from backend.schemas.tag import CreateTagSchema
from backend.schemas.tag_object import CreateTagObjectSchema
from backend.schemas.service import CreateServiceSchema
from backend.schemas.login import LoginSchema
from backend.schemas.create_user import CreateUserSchema
from backend.schemas.tenant import CreateTenantSchema
from backend.schemas.message import MessageSchema
from backend.schemas.rule import CreateRuleSchema
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.service_group_member import ServiceGroupMember
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.helper_user_tenant import (
    is_superadmin,
    can_read_tenant,
)
from backend.services.membership import (
    add_address_to_group,
    add_filter_to_interface,
    add_objects_to_rule,
    add_rule_to_filter,
    add_service_to_group,
    add_addresses_to_group,
    add_services_to_group,
    add_devices_to_group,
)
from backend.utils.logger import set_up_logger


# Logger setup
logger = set_up_logger(__name__)


api = NinjaAPI(auth=None if settings.DEBUG else django_auth)

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


"""
====================================================================
Tests
====================================================================
"""


@api.get("/hello", tags=["Debugging"])
def hello(request):
    return "Hello world"


# This is a temporary endpoint to set the tenant ID in the session for testing purposes. In a real implementation, this would be handled by an authentication system and middleware.
@api.get(
    "/set_tenant",
    tags=["Debugging"],
    response={200: dict, 404: MessageSchema},
)
def set_tenant(request, tenant_id: str):
    try:
        Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.warning(f"Tried to set tenant_id={tenant_id}, but it does not exist.")
        return Status(404, {"status": "error", "message": f"Tenant with id {tenant_id} does not exist."})
    request.session["current_tenant_id"] = tenant_id
    request.session.modified = True
    logger.info(f"Tenant ID set to {tenant_id} in session")
    return Status(200, {"message": f"Tenant set to {tenant_id}"})


"""
====================================================================
Attributes
====================================================================
"""


@api.get(
    "/get_address_group_and_addresses",
    tags=["Attributes - Address"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenantd
def get_address_group_and_addresses_endpoint(request):
    result, _, _ = get_address_groups_and_addresses_from_tenant(
        request.user,
        request.session["current_tenant_id"],
    )
    return Status(200, result)


@api.get(
    "/get_addresses_and_groups_with_tags",
    tags=["Attributes - Address"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenantd
def get_addresses_and_groups_with_tags_endpoint(request):
    response = get_all_addresses_and_groups_with_tags_from_tenant(request.user, request.session["current_tenant_id"])
    return Status(200, response)


@api.get("/list_addresses", tags=["Attributes - Address"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def list_addresses(request):
    addresses = Address.objects.filter(tenant_id=request.session["current_tenant_id"])
    return Status(200, list(addresses.values()))


@api.post(
    "/create_address",
    tags=["Attributes - Address"],
    response={200: dict, 403: MessageSchema},
)
@require_write_tenantd
def create_address_endpoint(
    request,
    payload: CreateAddressSchema,
):
    address = create_address(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        addr_type=payload.addr_type,
        ipv4_type=payload.ipv4_type,
        ipv6_type=payload.ipv6_type,
        ipv4Network=payload.ipv4Network,
        ipv6Network=payload.ipv6Network,
        ipv4Address_start=payload.ipv4Address_start,
        ipv4Address_end=payload.ipv4Address_end,
        ipv6Address_start=payload.ipv6Address_start,
        ipv6Address_end=payload.ipv6Address_end,
    )
    logger.info(f"create_address endpoint succeeded for address id={address.id}")
    return Status(
        200,
        {
            "id": address.id,
            "name": address.name,
            "description": address.description,
            "addr_type": address.addr_type,
            "ipv4_type": address.ipv4_type,
            "ipv6_type": address.ipv6_type,
            "ipv4Network": str(address.ipv4Network) if address.ipv4Network else None,
            "ipv6Network": str(address.ipv6Network) if address.ipv6Network else None,
            "ipv4Address_start": str(address.ipv4Address_start) if address.ipv4Address_start else None,
            "ipv4Address_end": str(address.ipv4Address_end) if address.ipv4Address_end else None,
            "ipv6Address_start": str(address.ipv6Address_start) if address.ipv6Address_start else None,
            "ipv6Address_end": str(address.ipv6Address_end) if address.ipv6Address_end else None,
        },
    )


@api.post(
    "/create_address_group",
    tags=["Attributes - Address"],
    response={200: dict, 403: MessageSchema},
)
@require_write_tenantd
def create_address_group_endpoint(request, payload: CreateGroupSchema):
    address_group = create_address_group(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
    )
    logger.info(f"create_address_group endpoint succeeded for group id={address_group.id}")
    return Status(
        200,
        {
            "id": address_group.id,
            "name": address_group.name,
            "description": address_group.description,
        },
    )


@api.post(
    "/add_address_to_group",
    tags=["Attributes - Address"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def add_address_to_group_endpoint(request, address_id: int, group_id: int):
    try:
        AddressGroup.objects.get(id=group_id)
    except AddressGroup.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address group id={group_id} not found.",
            },
        )
    try:
        Address.objects.get(id=address_id)
    except Address.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address id={address_id} not found.",
            },
        )
    add_address_to_group(request.user, request.session["current_tenant_id"], group_id, address_id)
    logger.info(f"add_address_to_group endpoint succeeded for address id={address_id} and group id={group_id}")
    return Status(200, {"status": "success", "group_id": group_id, "address_id": address_id})


@api.post(
    "/add_addresses_to_group",
    tags=["Attributes - Address"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def add_addresses_to_group_endpoint(request, address_ids: list[int], group_id: int):
    try:
        AddressGroup.objects.get(id=group_id)
    except AddressGroup.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address group id={group_id} not found.",
            },
        )

    response = add_addresses_to_group(request.user, request.session["current_tenant_id"], group_id, address_ids)

    logger.info(
        f"add_addresses_to_group endpoint succeeded for "
        f"address ids={response['added_address_ids']} and group id={group_id}"
    )

    return Status(
        200,
        {
            "status": "success",
            "group_id": group_id,
            "added_address_ids": response["added_address_ids"],
            "already_present_address_ids": response["already_present_address_ids"],
            "not_found_address_ids": response["not_found_address_ids"],
        },
    )


@api.post(
    "/create_and_add_address_to_groups",
    tags=["Attributes - Address"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def create_and_add_address_to_groups_endpoint(request, payload: CreateAddressSchema, group_ids: list[int]):
    try:
        for group_id in group_ids:
            AddressGroup.objects.get(id=group_id)
    except AddressGroup.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address group id={group_id} not found.",
            },
        )
    address = create_and_add_address_to_groups(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        addr_type=payload.addr_type,
        ipv4_type=payload.ipv4_type,
        ipv6_type=payload.ipv6_type,
        ipv4Network=payload.ipv4Network,
        ipv6Network=payload.ipv6Network,
        ipv4Address_start=payload.ipv4Address_start,
        ipv4Address_end=payload.ipv4Address_end,
        ipv6Address_start=payload.ipv6Address_start,
        ipv6Address_end=payload.ipv6Address_end,
        group_ids=group_ids,
    )
    logger.info(f"create_and_add_address_to_groups endpoint succeeded for address id={address.id}")
    return Status(
        200,
        {
            "address_id": address.id,
            "group_ids": group_ids,
        },
    )


@api.post(
    "/create_address_group_and_add_addresses",
    tags=["Attributes - Address"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def create_address_group_and_add_addresses_endpoint(request, payload: CreateGroupSchema, address_ids: list[int]):
    try:
        for address_id in address_ids:
            Address.objects.get(id=address_id)
    except Address.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address id={address_id} not found.",
            },
        )
    address_group = create_address_group_and_add_addresses(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        members=address_ids,
    )
    logger.info(f"create_address_group_and_add_addresses endpoint succeeded for address group id={address_group.id}")
    return Status(
        200,
        {
            "address_group_id": address_group.id,
            "address_ids": address_ids,
        },
    )


@api.delete(
    "/delete_address",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def delete_address_endpoint(request, address_id: int):
    try:
        address = Address.objects.get(id=address_id, tenant_id=request.session["current_tenant_id"])
        address.delete()
        logger.info(f"Address deleted: {address}")
        return Status(
            200,
            {
                "status": "success",
                "message": f"Address with id {address_id} deleted.",
            },
        )
    except Address.DoesNotExist:
        logger.warning(f"Tried to delete address with id {address_id}, but it does not exist.")
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address with id {address_id} does not exist.",
            },
        )


@api.delete(
    "/delete_address_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def delete_address_group_endpoint(request, group_id: int):
    try:
        address_group = AddressGroup.objects.get(id=group_id, tenant_id=request.session["current_tenant_id"])
        address_group.delete()
        logger.info(f"Address Group deleted: {address_group}")
        return Status(
            200,
            {
                "status": "success",
                "message": f"Address Group with id {group_id} deleted.",
            },
        )
    except AddressGroup.DoesNotExist:
        logger.warning(f"Tried to delete address group with id {group_id}, but it does not exist.")
        return Status(
            404,
            {
                "status": "error",
                "message": f"Address Group with id {group_id} does not exist.",
            },
        )


@api.get("/list_services", tags=["Attributes - Service"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def list_services(request):
    services = Service.objects.filter(tenant_id=request.session["current_tenant_id"])
    return Status(200, list(services.values()))


@api.get(
    "/get_service_group_and_services",
    tags=["Attributes - Service"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenantd
def get_service_group_and_services_endpoint(request):
    if not can_read_tenant(request.user, request.session["current_tenant_id"]):
        logger.warning(
            f"Unauthorized attempt to read services from tenant={request.session['current_tenant_id']} "
            f"by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to read services from this tenant.",
        }
    result, _, _ = get_service_groups_and_services_from_tenant(
        request.user,
        request.session["current_tenant_id"],
    )
    return Status(200, result)


@api.get(
    "/get_services_and_groups_with_tags",
    tags=["Attributes - Service"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenantd
def get_services_and_groups_with_tags_endpoint(request):
    response = get_all_services_and_groups_with_tags_from_tenant(request.user, request.session["current_tenant_id"])
    return Status(200, response)


@api.post(
    "/create_service",
    tags=["Attributes - Service"],
    response={200: dict, 403: MessageSchema},
)
@require_write_tenantd
def create_service_endpoint(
    request,
    payload: CreateServiceSchema,
):
    service = create_service(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        protocol=payload.protocol,
        port_start=payload.port_start,
        port_end=payload.port_end,
    )
    logger.info(f"create_service endpoint succeeded for service id={service.id}")
    return Status(
        200,
        {
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "protocol": service.protocol,
            "port_start": service.port_start,
            "port_end": service.port_end,
        },
    )


@api.post("/create_service_group", tags=["Attributes - Service"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def create_service_group_endpoint(request, payload: CreateGroupSchema):

    service_group = create_service_group(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
    )
    logger.info(f"Service Group created: {service_group}")
    return Status(
        200,
        {
            "id": service_group.id,
            "name": service_group.name,
            "description": service_group.description,
        },
    )


@api.post(
    "/add_service_to_group", tags=["Attributes - Service"], response={200: dict, 403: MessageSchema, 404: MessageSchema}
)
def add_service_to_group_endpoint(request, service_id: int, group_id: int):
    try:
        ServiceGroup.objects.get(id=group_id)
    except ServiceGroup.DoesNotExist:
        return 404, {
            "status": "error",
            "message": f"Service group id={group_id} not found.",
        }

    add_service_to_group(request.user, request.session["current_tenant_id"], group_id, service_id)
    logger.info(f"add_service_to_group endpoint succeeded for service id={service_id} and group id={group_id}")
    return Status(
        200,
        {
            "service_id": service_id,
            "group_id": group_id,
        },
    )


@api.post(
    "/add_services_to_group",
    tags=["Attributes - Service"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def add_services_to_group_endpoint(request, service_ids: list[int], group_id: int):
    try:
        ServiceGroup.objects.get(id=group_id)
    except ServiceGroup.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Service group id={group_id} not found.",
            },
        )

    response = add_services_to_group(request.user, request.session["current_tenant_id"], group_id, service_ids)

    logger.info(
        f"add_services_to_group endpoint succeeded for "
        f"service ids={response['added_service_ids']} and group id={group_id}"
    )

    return Status(
        200,
        {
            "group_id": group_id,
            "added_service_ids": response["added_service_ids"],
            "already_present_service_ids": response["already_present_service_ids"],
            "not_found_service_ids": response["not_found_service_ids"],
        },
    )


@api.post(
    "/create_and_add_service_to_groups",
    tags=["Attributes - Service"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def create_and_add_service_to_groups_endpoint(request, payload: CreateServiceSchema, group_ids: list[int]):
    try:
        for group_id in group_ids:
            ServiceGroup.objects.get(id=group_id)
    except ServiceGroup.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Service group id={group_id} not found.",
            },
        )
    service = create_and_add_service_to_groups(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        protocol=payload.protocol,
        port_start=payload.port_start,
        port_end=payload.port_end,
        group_ids=group_ids,
    )
    return Status(
        200,
        {
            "service_id": service.id,
            "group_ids": group_ids,
        },
    )


@api.post(
    "/create_service_group_and_add_services",
    tags=["Attributes - Service"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def create_service_group_and_add_services_endpoint(request, payload: CreateGroupSchema, service_ids: list[int]):
    try:
        for service_id in service_ids:
            Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Service id={service_id} not found.",
            },
        )
    service_group = create_service_group_and_add_services(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        members=service_ids,
    )
    return Status(
        200,
        {
            "group_id": service_group.id,
            "service_ids": service_ids,
        },
    )


@api.delete(
    "/delete_service",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def delete_service_endpoint(request, service_id: int):
    try:
        service = Service.objects.get(id=service_id, tenant_id=request.session["current_tenant_id"])
        service.delete()
        logger.info(f"Service deleted: {service}")
        return Status(
            200,
            {
                "status": "success",
                "message": f"Service with id {service_id} deleted.",
            },
        )
    except Service.DoesNotExist:
        logger.warning(f"Tried to delete service with id {service_id}, but it does not exist.")
        return Status(
            404,
            {
                "status": "error",
                "message": f"Service with id {service_id} does not exist.",
            },
        )


@api.delete(
    "/delete_service_group",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def delete_service_group_endpoint(request, group_id: int):
    try:
        service_group = ServiceGroup.objects.get(id=group_id, tenant_id=request.session["current_tenant_id"])
        service_group.delete()
        logger.info(f"Service Group deleted: {service_group}")
        return Status(
            200,
            {
                "status": "success",
                "message": f"Service Group with id {group_id} deleted.",
            },
        )
    except ServiceGroup.DoesNotExist:
        logger.warning(f"Tried to delete service group with id {group_id}, but it does not exist.")
        return Status(
            404,
            {
                "status": "error",
                "message": f"Service Group with id {group_id} does not exist.",
            },
        )


@api.get("/get_all_tags_from_object", tags=["Attributes - Tag"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def get_all_tags_from_object_endpoint(request, object_id: int, object_type: str):
    tags = get_all_tags_from_object(request.user, request.session["current_tenant_id"], object_id, object_type)
    return Status(
        200,
        [
            {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "tenant_id": tag.tenant_id,
            }
            for tag in tags
        ],
    )


@api.get("/get_all_tags_from_tenant", tags=["Attributes - Tag"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def get_all_tags_from_tenant_endpoint(request):
    tags = get_all_tags_from_tenant(request.user, request.session["current_tenant_id"])
    return Status(
        200,
        [
            {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "tenant_id": tag.tenant_id,
            }
            for tag in tags
        ],
    )


@api.post("/create_tag", tags=["Attributes - Tag"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def create_tag_endpoint(request, payload: CreateTagSchema):
    tag = create_tag(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
    )
    logger.info(f"create_tag endpoint succeeded for tag id={tag.id}")
    return Status(
        200,
        {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "tenant_id": tag.tenant_id,
        },
    )


@api.post(
    "/create_and_add_tag_to_object",
    tags=["Attributes - Tag"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def create_and_add_tag_to_object_endpoint(request, payload: CreateTagObjectSchema):
    try:
        DJANGO_MODEL_MAPPING[payload.object_type.lower()].objects.get(id=payload.object_id)
    except KeyError:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Object type '{payload.object_type}' is not recognized.",
            },
        )
    except DJANGO_MODEL_MAPPING[payload.object_type.lower()].DoesNotExist:
        return Status(
            404,
            {
                "status": "error",
                "message": f"Object with id={payload.object_id} of type '{payload.object_type}' not found.",
            },
        )
    tag = create_and_add_tag_to_object(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        tag_name=payload.name,
        tag_description=payload.description,
        object_type=payload.object_type,
        object_id=payload.object_id,
    )
    logger.info(
        f"create_and_add_tag_to_object endpoint succeeded for tag id={tag.id} and object id={payload.object_id}"
    )
    return Status(
        200,
        {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "tenant_id": tag.tenant_id,
            "object_id": payload.object_id,
            "object_type": payload.object_type,
        },
    )


@api.delete("/clear_all_tags_from_object", tags=["Attributes - Tag"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def clear_all_tags_from_object_endpoint(request, object_id: int, object_type: str):
    deleted_count = clear_all_tags_from_object(
        request.user, request.session["current_tenant_id"], object_id, object_type
    )
    logger.info(
        f"clear_all_tags_from_object endpoint succeeded for object id={object_id} and object type={object_type}. Deleted {deleted_count} tag connections."
    )
    return Status(
        200,
        {
            "deleted_count": deleted_count,
            "object_id": object_id,
            "object_type": object_type,
        },
    )


@api.delete("/remove_tag_from_object", tags=["Attributes - Tag"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def remove_tag_from_object_endpoint(request, object_id: int, object_type: str, tag_id: int):
    deleted_count = remove_tag_from_object(
        request.user, request.session["current_tenant_id"], object_id, object_type, tag_id
    )
    logger.info(
        f"remove_tag_from_object endpoint succeeded for tag id={tag_id} and object id={object_id} of type {object_type}. Deleted {deleted_count} tag connections."
    )
    return Status(
        200,
        {
            "deleted_count": deleted_count,
            "object_id": object_id,
            "object_type": object_type,
            "tag_id": tag_id,
        },
    )


@api.delete("/delete_tag_from_tenant", tags=["Attributes - Tag"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def delete_tag_from_tenant_endpoint(request, tag_id: int):
    deleted_count = delete_tag_from_tenant(request.user, request.session["current_tenant_id"], tag_id)
    logger.info(
        f"delete_tag_from_tenant endpoint succeeded for tag id={tag_id} in tenant={request.session['current_tenant_id']}. Deleted {deleted_count} tag connections."
    )
    return Status(
        200,
        {
            "deleted_count": deleted_count,
            "tag_id": tag_id,
            "tenant_id": request.session["current_tenant_id"],
        },
    )


"""
====================================================================
Management Objects
====================================================================
"""


@api.post("/create_tenant", tags=["Management - Tenant"], response={200: dict, 403: MessageSchema})
@require_superadmind
def create_tenant_endpoint(request, payload: CreateTenantSchema):
    tenant = create_tenant(request.user, payload.name)
    logger.info(f"create_tenant endpoint succeeded for tenant id={tenant.id}")
    return Status(
        200,
        {
            "tenant_id": tenant.id,
            "tenant_name": tenant.tenant_name,
        },
    )


@api.get("/list_tenants", tags=["Management - Tenant"], response={200: list[dict], 403: MessageSchema})
@require_superadmind
def list_tenants(request):
    tenants = Tenant.objects.all()
    return Status(200, list(tenants.values()))


@api.delete(
    "/delete_tenant",
    tags=["Management - Tenant"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_superadmind
def delete_tenant_endpoint(request, tenant_id: int):
    delete_tenant(request.user, tenant_id)
    logger.info(f"delete_tenant endpoint succeeded for tenant id={tenant_id}")
    return Status(
        200,
        {
            "deleted_tenant_id": tenant_id,
            "message": f"Tenant with id {tenant_id} deleted.",
        },
    )


@api.get("/list_devices", tags=["Management - Device"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def list_devices(request):
    devices = get_all_devices_from_tenant(request.user, request.session["current_tenant_id"])
    return Status(200, list(devices.values()))


@api.get(
    "/get_interfaces_for_device",
    tags=["Management - Device"],
    response={200: list[dict], 403: MessageSchema, 404: MessageSchema},
)
@require_read_tenantd
def get_interfaces_for_device_endpoint(request, device_id: int):
    try:
        interfaces = get_all_interfaces_from_device(request.user, request.session["current_tenant_id"], device_id)
        return Status(
            200,
            [
                {
                    "id": interface.id,
                    "name": interface.name,
                    "description": interface.description,
                    "device_id": interface.device_id,
                    "type": interface.type,
                    "VRF": interface.VRF,
                }
                for interface in interfaces
            ],
        )
    except Exception as e:
        logger.error(f"Error retrieving interfaces for device with id {device_id}: {str(e)}")
        return Status(
            403,
            {
                "status": "error",
                "message": f"Error retrieving interfaces for device with id {device_id}: {str(e)}",
            },
        )


@api.post("/create_device", tags=["Management - Device"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def create_device_endpoint(request, payload: CreateDeviceSchema):
    try:
        device = create_device(
            actor=request.user,
            tenant_id=request.session["current_tenant_id"],
            name=payload.name,
            platform=payload.platform,
            description=payload.description,
            type=payload.type,
        )
        logger.info(f"create_device endpoint succeeded for device id={device.id}")
        return Status(
            200,
            {
                "device_id": device.id,
                "device_name": device.name,
                "device_platform": device.platform,
                "device_description": device.description,
                "device_type": device.type,
            },
        )
    except Exception as e:
        logger.error(f"create_device endpoint failed: {str(e)}")
        return Status(
            403,
            {
                "message": "Device creation failed",
                "status": str(e),
            },
        )


@api.post(
    "/create_device_and_add_it_to_group",
    tags=["Management - Device"],
    response={200: dict, 403: MessageSchema},
)
@require_write_tenantd
def create_device_and_add_it_to_group(request, payload: CreateDeviceSchema, group_id: int):
    device = create_device(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        platform=payload.platform,
        description=payload.description,
        type=payload.type,
    )
    add_devices_to_group(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        group_id=group_id,
        device_ids=[device.id],
    )
    logger.info(
        f"create_device_and_add_it_to_group endpoint succeeded for device id={device.id} and group id={group_id}"
    )
    return Status(
        200,
        {
            "device_id": device.id,
            "device_name": device.name,
            "device_platform": device.platform,
            "device_description": device.description,
            "device_type": device.type,
            "group_id": group_id,
        },
    )


@api.post("/create_device_group", tags=["Management - Device"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def create_device_group_endpoint(request, payload: CreateGroupSchema):
    device_group = create_device_group(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
    )
    logger.info(f"create_device_group endpoint succeeded for device group id={device_group.id}")
    return Status(
        200,
        {
            "device_group_id": device_group.id,
            "device_group_name": device_group.name,
            "device_group_description": device_group.description,
        },
    )


@api.post(
    "/add_devices_to_group",
    tags=["Management - Device"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def add_devices_to_group_endpoint(request, device_ids: list[int], group_id: int):
    response = add_devices_to_group(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        device_group_id=group_id,
        device_ids=device_ids,
    )

    logger.info(
        f"add_devices_to_group endpoint succeeded for device ids={response['added_device_ids']} and group id={group_id}"
    )
    if response["not_found_device_ids"]:
        logger.warning(
            f"Some device ids were not found when adding to group id={group_id}: {response['not_found_device_ids']}"
        )
        return Status(
            404,
            {
                "status": "error",
                "message": (
                    f"Processed device ids for group id={group_id}. "
                    f"Added={response['added_device_ids']}, "
                    f"already_present={response['already_present_device_ids']}, "
                    f"not_found={response['not_found_device_ids']}"
                ),
            },
        )
    return Status(
        200,
        {
            "group_id": group_id,
            "added_device_ids": response["added_device_ids"],
            "already_present_device_ids": response["already_present_device_ids"],
            "not_found_device_ids": response["not_found_device_ids"],
        },
    )


@api.post(
    "/create_interface",
    tags=["Management - Device"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def create_interface_endpoint(request, payload: CreateInterfaceSchema):
    try:
        interface = create_interface(
            actor=request.user,
            tenant_id=request.session["current_tenant_id"],
            name=payload.name,
            description=payload.description,
            device_id=payload.device_id,
            type=payload.type,
            VRF=payload.VRF,
        )
        logger.info(f"create_interface endpoint succeeded for interface id={interface.id}")
        return Status(
            200,
            {
                "interface_id": interface.id,
                "interface_name": interface.name,
                "interface_description": interface.description,
            },
        )
    except Exception as e:
        logger.error(f"create_interface endpoint failed: {str(e)}")
        return Status(
            403,
            {
                "message": "Interface creation failed",
                "status": str(e),
            },
        )


@api.delete(
    "/delete_device",
    tags=["Management - Device"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def delete_device_endpoint(request, device_id: int):
    try:
        response = delete_device(request.user, request.session["current_tenant_id"], device_id)
    except Exception as e:
        logger.error(f"Error deleting device with id {device_id}: {str(e)}")
        return Status(
            403,
            {
                "status": "error",
                "message": f"Error deleting device with id {device_id}: {str(e)}",
            },
        )
    logger.info(f"Device deleted: {response['device']}")
    return Status(
        200,
        {
            "deleted_device_id": device_id,
        },
    )


@api.delete(
    "/delete_interface",
    tags=["Management - Device"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def delete_interface_endpoint(request, interface_id: int):
    try:
        response = delete_interface(request.user, request.session["current_tenant_id"], interface_id)
        logger.info(f"Interface deleted: {response['interface']}")
        return Status(
            200,
            {
                "deleted_interface_id": interface_id,
            },
        )
    except Exception as e:
        logger.error(f"Error deleting interface with id {interface_id}: {str(e)}")
        return Status(
            403,
            {
                "status": "error",
                "message": f"Error deleting interface with id {interface_id}: {str(e)}",
            },
        )


"""
====================================================================
Filter Objects
====================================================================
"""


@api.get("/list_rules", tags=["Filter - Rule"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def list_rules(request):
    rules = get_all_rules_from_tenant(request.user, request.session["current_tenant_id"])
    return Status(200, list(rules.values()))


@api.get("/list_rules_with_objects", tags=["Filter - Rule"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def list_rules_with_objects(request):
    rules = get_all_rules_with_objects_from_tenant(request.user, request.session["current_tenant_id"])
    return Status(200, rules)


@api.post("/create_rule", tags=["Filter - Rule"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def create_rule_endpoint(request, payload: CreateRuleSchema):
    rule = create_rule(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
        action=payload.action,
        log_type=payload.log_type,
        hit_count=0,
    )
    logger.info(f"create_rule endpoint succeeded for rule id={rule.id}")
    return Status(
        200,
        {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "rule_description": rule.description,
        },
    )


@api.post(
    "/add_object_to_rule",
    tags=["Configuration"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def add_object_to_rule_endpoint(request, rule_id: int, match_type: str, object_type: str, object_ids: list[int]):
    try:
        objects = [DJANGO_MODEL_MAPPING[object_type.lower()].objects.get(id=obj_id) for obj_id in object_ids]
        add_objects_to_rule(
            actor=request.user,
            tenant_id=request.session["current_tenant_id"],
            rule_id=rule_id,
            match_type=match_type,
            objects=objects,
        )
        logger.info(f"add_object_to_rule endpoint succeeded for rule id={rule_id}")
        return Status(
            200,
            {
                "rule_id": rule_id,
                "match_type": match_type,
                "object_type": object_type,
                "object_ids": object_ids,
            },
        )
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


@api.delete("/delete_rule", tags=["Filter - Rule"], response={200: dict, 403: MessageSchema, 404: MessageSchema})
@require_write_tenantd
def delete_rule_endpoint(request, rule_id: int):
    try:
        delete_rule(request.user, request.session["current_tenant_id"], rule_id)
        logger.info(f"Rule deleted: id={rule_id}")
        return Status(
            200,
            {
                "rule_id": rule_id,
            },
        )
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


@api.post("/add_rule_to_filter", tags=["Configuration"], response={200: dict, 403: MessageSchema, 404: MessageSchema})
@require_write_tenantd
def add_rule_to_filter_endpoint(request, filter_id: int, rule_id: int, rule_sequence: int):
    try:
        add_rule_to_filter(
            actor=request.user,
            tenant_id=request.session["current_tenant_id"],
            rule_id=rule_id,
            filter_id=filter_id,
            rule_sequence=rule_sequence,
        )
        logger.info(f"Rule id={rule_id} added to filter id={filter_id} with rule_sequence={rule_sequence}")
        return Status(
            200,
            {
                "rule_id": rule_id,
                "filter_id": filter_id,
                "rule_sequence": rule_sequence,
            },
        )
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


@api.post("/create_filter", tags=["Filter - Filter"], response={200: dict, 403: MessageSchema, 404: MessageSchema})
@require_write_tenantd
def create_filter_endpoint(request, payload: CreateFilterSchema):
    filter_obj = create_filter(
        actor=request.user,
        tenant_id=request.session["current_tenant_id"],
        name=payload.name,
        description=payload.description,
    )
    logger.info(f"create_filter endpoint succeeded for filter id={filter_obj.id}")
    return Status(
        200,
        {
            "filter_id": filter_obj.id,
        },
    )


@api.delete("/delete_filter", tags=["Filter - Filter"], response={200: dict, 403: MessageSchema, 404: MessageSchema})
@require_write_tenantd
def delete_filter_endpoint(request, filter_id: int):
    try:
        delete_filter(actor=request.user, tenant_id=request.session["current_tenant_id"], filter_id=filter_id)
        logger.info(f"Filter deleted: id={filter_id}")
        return Status(
            200,
            {
                "filter_id": filter_id,
            },
        )
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


@api.get(
    "/get_filters_from_interface",
    tags=["Filter - Filter"],
    response={200: list[dict], 403: MessageSchema, 404: MessageSchema},
)
@require_read_tenantd
def get_filters_from_interface_endpoint(request, interface_id: int):
    try:
        filters = get_all_filters_from_interface(
            actor=request.user, tenant_id=request.session["current_tenant_id"], interface_id=interface_id
        )
        return Status(200, list(filters.values()))
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


@api.get("/get_all_filters_from_tenant", tags=["Filter - Filter"], response={200: list[dict], 403: MessageSchema})
@require_read_tenantd
def get_all_filters_from_tenant_endpoint(request):
    filters = get_all_filters_from_tenant(actor=request.user, tenant_id=request.session["current_tenant_id"])
    return Status(200, list(filters.values()))


@api.post(
    "/add_filter_to_interface",
    tags=["Configuration"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def add_filter_to_interface_endpoint(
    request, filter_id: int, interface_id: int, policy_sequence: int, enable: bool, direction: str
):
    """
    Adds a filter object to the interface object. Importantly this does not generate or apply a configuration to the interface.
    """
    try:
        add_filter_to_interface(
            actor=request.user,
            tenant_id=request.session["current_tenant_id"],
            filter_id=filter_id,
            interface_id=interface_id,
            policy_sequence=policy_sequence,
            enable=enable,
            direction=direction,
        )
        logger.info(
            f"Filter id={filter_id} added to interface id={interface_id} with policy_sequence={policy_sequence} and enable={enable}"
        )
        return Status(
            200,
            {
                "filter_id": filter_id,
                "interface_id": interface_id,
                "policy_sequence": policy_sequence,
                "enable": enable,
                "direction": direction,
            },
        )
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


@api.post("/add_test_data", tags=["Debugging"], response={200: dict, 403: MessageSchema})
@require_write_tenantd
def add_test_data(request):
    create_interfaces_devices_devicegroups_tags(actor=request.user, tenant_id=request.session["current_tenant_id"])
    Tenant.objects.get_or_create(tenant_name="NTNU")
    Tenant.objects.get_or_create(tenant_name="Sikt")
    Tenant.objects.get_or_create(tenant_name="UiO")
    return Status(
        200,
        {
            "status": "success",
            "message": "Test data added successfully",
        },
    )


@api.get(
    "/generate_config_for_interface",
    tags=["Configuration"],
    response={200: dict, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenantd
def generate_config_for_interface(request, interface_id: int, direction: str):
    try:
        policies = create_policies_for_interface(
            actor=request.user,
            tenant_id=request.session["current_tenant_id"],
            interface_id=interface_id,
            direction=direction,
        )
        logger.info(f"Created policies for interface id={interface_id}")
        logger.info(f"Policies for interface id={interface_id}: {[policy.YAMLConfig for policy in policies]}")
        logger.info(f"Networks for interface id={interface_id}: {[policy.networks for policy in policies]}")
        logger.info(f"Services for interface id={interface_id}: {[policy.services for policy in policies]}")
        config = generate_multi_policy_config(policies)
        logger.info(f"Generated configuration for interface id={interface_id}: {config}")
        return Status(
            200,
            {
                "status": "success",
                "message": f"Configuration generated for interface id={interface_id}",
                "policies": [policy.YAMLConfig for policy in policies],
                "config": str(config),
            },
        )
    except ValueError as e:
        logger.warning(str(e))
        return Status(
            404,
            {
                "status": "error",
                "message": str(e),
            },
        )


"""
====================================================================
User Management
====================================================================
"""


@api.post("/login", tags=["Authentication - User"], auth=None, response={200: dict, 401: MessageSchema})
def login_endpoint(request, payload: LoginSchema):
    user = authenticate(request, username=payload.username, password=payload.password)

    if user is None:
        logger.warning(f"Failed login attempt for username={payload.username}")
        return Status(
            401,
            {
                "status": "error",
                "message": "Invalid username or password",
            },
        )

    login(request, user)
    logger.info(f"User logged in: {user.username}")

    if not user.is_superuser:
        if TenantUserMember.objects.filter(user_id=user.id).exists():
            request.session["current_tenant_id"] = TenantUserMember.objects.get(user_id=user.id).tenant_id

    return Status(
        200,
        {
            "status": "success",
            "message": "Logged in successfully",
            "username": user.username,
            "is_superuser": user.is_superuser,
            "session_key": request.session.session_key,
        },
    )


@api.post("/logout", tags=["Authentication - User"], auth=None, response={200: dict})
def logout_endpoint(request):
    username = request.user.username if request.user.is_authenticated else "anonymous"
    logout(request)
    logger.info(f"User logged out: {username}")
    return Status(200, {"status": "success", "message": "Logged out successfully"})


@api.get("/who_am_i", tags=["Authentication - User"], auth=None, response={200: dict})
def who_am_i(request):
    if request.user.is_authenticated:
        return Status(
            200,
            {
                "authenticated": True,
                "username": request.user.username,
                "email": request.user.email,
                "id": request.user.id,
                "current_tenant_id": request.session.get("current_tenant_id"),
                "is_superuser": request.user.is_superuser,
                "permissions": TenantUserMember.objects.filter(user_id=request.user.id).values_list("role", flat=True)
                if not request.user.is_superuser
                else ["superadmin"],
            },
        )

    return Status(
        200,
        {
            "authenticated": False,
            "username": None,
            "email": None,
            "id": None,
        },
    )


@api.get("/get_users", tags=["User Management"], response={200: dict})
@require_superadmind
def get_users(request):
    users = []

    for user in User.objects.all():
        user_data = {
            **user.__dict__,
            "permissions": list(TenantUserMember.objects.filter(user_id=user.id).values_list("role", flat=True)),
        }
        user_data.pop("_state", None)
        users.append(user_data)

    return Status(200, {"status": "success", "users": users})


@api.post("/create_user", tags=["User Management"], auth=None, response={200: dict, 400: dict})
@require_superadmind
def create_user(request, payload: CreateUserSchema):
    if User.objects.filter(username=payload.username).exists():
        return Status(
            400,
            {
                "status": "error",
                "message": f"User with username '{payload.username}' already exists.",
            },
        )

    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )

    for permission in payload.permissions:
        TenantUserMember.objects.create(user=user, tenant_id=payload.tenant_id, role=permission)

    logger.info(f"User created: {user.username}")
    return Status(
        200,
        {
            "status": "success",
            "message": f"User '{payload.username}' created successfully.",
            "user_id": user.id,
        },
    )


@api.delete("/delete_user", tags=["User Management"], response={200: dict, 400: dict})
@require_superadmind
def delete_user(request, user_id: int):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        logger.info(f"User deleted: {user}")
        return Status(200, {"status": "success", "message": f"User with id {user_id} deleted."})
    except User.DoesNotExist:
        logger.warning(f"Tried to delete user with id {user_id}, but it does not exist.")
        return Status(400, {"status": "error", "message": f"User with id {user_id} does not exist."})


# This endpoint allows a superadmin to add a user to a tenant with a specific role. Only superadmins can perform this action.
@api.post(
    "/add_tenant_privileges_to_user",
    tags=["User Management - Tenant"],
    response={200: MessageSchema, 403: MessageSchema},
)
@require_superadmind
def add_tenant_privileges_to_user_endpoint(request, payload: CreateTenantUserSchema):
    if not is_superadmin(request.user):
        logger.warning(
            f"Unauthorized attempt to create TenantUserMember for tenant_id={payload.tenant_id} and user_id={payload.user_id}"
        )
        return Status(
            403,
            {
                "status": "error",
                "message": "You do not have permission to add users to this tenant.",
            },
        )
    tenant_user = create_tenant_user_member(
        actor=request.user, tenant_id=payload.tenant_id, user_id=payload.user_id, role=payload.role
    )
    logger.info(
        f"create_tenant_user endpoint succeeded for tenant_id={payload.tenant_id} and user_id={payload.user_id}"
    )
    return Status(
        200,
        {
            "status": "success",
            "message": f"Tenant User created: {tenant_user}",
        },
    )
