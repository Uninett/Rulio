from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from ninja import NinjaAPI
from ninja.security import django_auth
from django.conf import settings

from backend.objects.attributes.service import Service
from backend.objects.management.device_group import DeviceGroup
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.schemas.address_group import CreateAddressGroupSchema
from backend.schemas.tenant_user import CreateTenantUserSchema
from backend.services.authentication import require_read_tenant, require_superadmin, require_write_tenant
from backend.services.delete import (
    clear_all_tags_from_object,
    delete_tag_from_tenant,
    remove_tag_from_object,
    delete_rule,
    delete_tenant,
)
from backend.services.get import (
    get_all_addresses_and_groups_with_tags,
    get_all_tags_from_object,
    get_service_groups_with_services_from_tenant,
    get_address_groups_with_addresses_from_tenant,
    get_all_tags_from_tenant,
    get_all_services_and_groups_with_tags,
    get_all_rules_from_tenant,
    get_all_rules_with_objects_from_tenant,
)
from backend.services.create import (
    create_address,
    create_and_add_tag_to_object,
    create_service,
    create_tag,
    create_tenant_user_member,
    create_tenant,
    create_address_group,
    create_service_group,
    create_rule,
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
from backend.objects.management.tenant import Tenant
from backend.services.helper_user_tenant import (
    is_superadmin,
    can_write_tenant,
    can_read_tenant,
)
from backend.services.membership import (
    add_address_to_group,
    add_objects_to_rule,
    add_service_to_group,
    add_addresses_to_group,
    add_services_to_group,
)
from backend.utils.logger import set_up_logger


api = NinjaAPI()

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
@api.get("/set_tenant", tags=["Debugging"])
def set_tenant(request, tenant_id: str):
    request.session["current_tenant_id"] = tenant_id
    request.session.modified = True
    logger.info(f"Tenant ID set to {tenant_id} in session")
    return {"message": f"Tenant set to {tenant_id}"}


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
@require_read_tenant
def get_address_group_and_addresses_endpoint(request, get="all"):
    response = get_address_groups_with_addresses_from_tenant(
        request.session["current_tenant_id"],
        get=get,
    )
    return 200, response


@api.get(
    "/get_addresses_and_groups_with_tags",
    tags=["Attributes - Address"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenant
def get_addresses_and_groups_with_tags_endpoint(request):
    response = get_all_addresses_and_groups_with_tags(request.session["current_tenant_id"])
    return 200, response


@api.get("/list_addresses", tags=["Attributes - Address"], response={200: list[dict], 403: MessageSchema})
@require_read_tenant
def list_addresses(request):
    addresses = Address.objects.filter(tenant_id=request.session["current_tenant_id"])
    return 200, list(addresses.values())


@api.post(
    "/create_address",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema},
)
@require_write_tenant
def create_address_endpoint(
    request,
    payload: CreateAddressSchema,
):
    address = create_address(
        request=request,
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
    logger.info(f"create_service endpoint succeeded for service id={address.id}")
    return 200, {
        "message": "Service created",
        "status": f"Service created with id {address.id}",
    }


@api.post(
    "/create_address_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema},
)
@require_write_tenant
def create_address_group_endpoint(request, payload: CreateAddressGroupSchema):
    address_group = create_address_group(request, payload.name, payload.description)
    logger.info(f"create_address_group endpoint succeeded for group id={address_group.id}")
    return 200, {
        "status": "success",
        "message": f"Address Group created: {address_group}",
    }


@api.post(
    "/add_address_to_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema},
)
@require_write_tenant
def add_address_to_group_endpoint(request, address_id: int, group_id: int):
    if not can_write_tenant(
        request.user,
        Tenant.objects.get(id=AddressGroup.objects.get(id=group_id).tenant_id),
    ):
        logger.warning(
            f"Unauthorized attempt to add address id={address_id} to group id={group_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to modify this address group.",
        }
    add_address_to_group(request, group_id, address_id)
    logger.info(f"add_address_to_group endpoint succeeded for address id={address_id} and group id={group_id}")
    return 200, {
        "status": "success",
        "message": f"Address id={address_id} added to group id={group_id}",
    }


@api.post(
    "/add_addresses_to_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def add_addresses_to_group_endpoint(request, address_ids: list[int], group_id: int):
    try:
        address_group = AddressGroup.objects.get(id=group_id)
    except AddressGroup.DoesNotExist:
        return 404, {
            "status": "error",
            "message": f"Address group id={group_id} not found.",
        }

    if not can_write_tenant(request.user, address_group.tenant_id):
        logger.warning(
            f"Unauthorized attempt to add addresses id={address_ids} "
            f"to group id={group_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to modify this address group.",
        }

    response = add_addresses_to_group(group_id, address_ids)

    logger.info(
        f"add_addresses_to_group endpoint succeeded for "
        f"address ids={response['added_address_ids']} and group id={group_id}"
    )

    return 200, {
        "status": "success",
        "message": (
            f"Processed address ids for group id={group_id}. "
            f"Added={response['added_address_ids']}, "
            f"already_present={response['already_present_address_ids']}, "
            f"not_found={response['not_found_address_ids']}"
        ),
    }


@api.delete(
    "/delete_address",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def delete_address_endpoint(request, address_id: int):
    try:
        address = Address.objects.get(id=address_id, tenant_id=request.session["current_tenant_id"])
        address.delete()
        logger.info(f"Address deleted: {address}")
        return 200, {
            "status": "success",
            "message": f"Address with id {address_id} deleted.",
        }
    except Address.DoesNotExist:
        logger.warning(f"Tried to delete address with id {address_id}, but it does not exist.")
        return 404, {
            "status": "error",
            "message": f"Address with id {address_id} does not exist.",
        }


@api.delete(
    "/delete_address_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def delete_address_group_endpoint(request, group_id: int):
    try:
        address_group = AddressGroup.objects.get(id=group_id, tenant_id=request.session["current_tenant_id"])
        address_group.delete()
        logger.info(f"Address Group deleted: {address_group}")
        return 200, {
            "status": "success",
            "message": f"Address Group with id {group_id} deleted.",
        }
    except AddressGroup.DoesNotExist:
        logger.warning(f"Tried to delete address group with id {group_id}, but it does not exist.")
        return 404, {
            "status": "error",
            "message": f"Address Group with id {group_id} does not exist.",
        }


@api.get("/list_services", tags=["Attributes - Service"], response={200: list[dict], 403: MessageSchema})
@require_read_tenant
def list_services(request):
    services = Service.objects.filter(tenant_id=request.session["current_tenant_id"])
    return 200, list(services.values())


@api.get(
    "/get_service_group_and_services",
    tags=["Attributes - Service"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenant
def get_service_group_and_services_endpoint(request, get="all"):
    if not can_read_tenant(request.user, request.session["current_tenant_id"]):
        logger.warning(
            f"Unauthorized attempt to read services from tenant={request.session['current_tenant_id']} "
            f"by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to read services from this tenant.",
        }
    response = get_service_groups_with_services_from_tenant(
        request.session["current_tenant_id"],
        get=get,
    )
    return 200, response


@api.get(
    "/get_services_and_groups_with_tags",
    tags=["Attributes - Service"],
    response={200: list[dict], 403: MessageSchema},
)
@require_read_tenant
def get_services_and_groups_with_tags_endpoint(request):
    response = get_all_services_and_groups_with_tags(request.session["current_tenant_id"])
    return 200, response


@api.post(
    "/create_service",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema},
)
@require_write_tenant
def create_service_endpoint(
    request,
    payload: CreateServiceSchema,
):
    service = create_service(
        request=request,
        name=payload.name,
        description=payload.description,
        protocol=payload.protocol,
        port_start=payload.port_start,
        port_end=payload.port_end,
    )
    logger.info(f"create_service endpoint succeeded for service id={service.id}")
    return 200, {
        "message": "Service created",
        "status": f"Service created with id {service.id}",
    }


@api.post("/create_service_group", tags=["Attributes - Service"])
@require_write_tenant
def create_service_group_endpoint(request, payload: CreateAddressGroupSchema):

    service_group = create_service_group(request, payload.name, payload.description)
    logger.info(f"Service Group created: {service_group}")
    return 200, {
        "status": "success",
        "message": f"Service Group created: {service_group}",
    }


@api.post("/add_service_to_group", tags=["Attributes - Service"], response={200: MessageSchema, 403: MessageSchema})
def add_service_to_group_endpoint(request, service_id: int, group_id: int):
    service_group = ServiceGroup.objects.get(id=group_id)
    if not can_write_tenant(request.user, Tenant.objects.get(id=service_group.tenant_id)) or not can_write_tenant(
        request.user,
        Tenant.objects.get(id=Service.objects.get(id=service_id).tenant_id),
    ):
        logger.warning(
            f"Unauthorized attempt to add service id={service_id} to group id={group_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to modify this service group.",
        }
    add_service_to_group(request, group_id, service_id)
    logger.info(f"add_service_to_group endpoint succeeded for service id={service_id} and group id={group_id}")
    return 200, {
        "status": "success",
        "message": f"Service id={service_id} added to group id={group_id}",
    }


@api.post(
    "/add_services_to_group",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def add_services_to_group_endpoint(request, service_ids: list[int], group_id: int):
    try:
        service_group = ServiceGroup.objects.get(id=group_id)
    except ServiceGroup.DoesNotExist:
        return 404, {
            "status": "error",
            "message": f"Service group id={group_id} not found.",
        }

    if not can_write_tenant(request.user, service_group.tenant_id):
        logger.warning(
            f"Unauthorized attempt to add services id={service_ids} "
            f"to group id={group_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to modify this service group.",
        }

    response = add_services_to_group(group_id, service_ids)

    logger.info(
        f"add_services_to_group endpoint succeeded for "
        f"service ids={response['added_service_ids']} and group id={group_id}"
    )

    return 200, {
        "status": "success",
        "message": (
            f"Processed service ids for group id={group_id}. "
            f"Added={response['added_service_ids']}, "
            f"already_present={response['already_present_service_ids']}, "
            f"not_found={response['not_found_service_ids']}"
        ),
    }


@api.delete(
    "/delete_service",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def delete_service_endpoint(request, service_id: int):
    try:
        service = Service.objects.get(id=service_id, tenant_id=request.session["current_tenant_id"])
        service.delete()
        logger.info(f"Service deleted: {service}")
        return 200, {
            "status": "success",
            "message": f"Service with id {service_id} deleted.",
        }
    except Service.DoesNotExist:
        logger.warning(f"Tried to delete service with id {service_id}, but it does not exist.")
        return 404, {
            "status": "error",
            "message": f"Service with id {service_id} does not exist.",
        }


@api.delete(
    "/delete_service_group",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def delete_service_group_endpoint(request, group_id: int):
    try:
        service_group = ServiceGroup.objects.get(id=group_id, tenant_id=request.session["current_tenant_id"])
        service_group.delete()
        logger.info(f"Service Group deleted: {service_group}")
        return 200, {
            "status": "success",
            "message": f"Service Group with id {group_id} deleted.",
        }
    except ServiceGroup.DoesNotExist:
        logger.warning(f"Tried to delete service group with id {group_id}, but it does not exist.")
        return 404, {
            "status": "error",
            "message": f"Service Group with id {group_id} does not exist.",
        }


@api.get("/get_all_tags_from_object", tags=["Attributes - Tag"], response={200: list[dict], 403: MessageSchema})
@require_read_tenant
def get_all_tags_from_object_endpoint(request, object_id: int, object_type: str):
    tags = get_all_tags_from_object(object_id, object_type)
    return 200, [
        {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "tenant_id": tag.tenant_id,
        }
        for tag in tags
    ]


@api.get("/get_all_tags_from_tenant", tags=["Attributes - Tag"], response={200: list[dict], 403: MessageSchema})
@require_read_tenant
def get_all_tags_from_tenant_endpoint(request):
    tags = get_all_tags_from_tenant(request.session["current_tenant_id"])
    return 200, [
        {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "tenant_id": tag.tenant_id,
        }
        for tag in tags
    ]


@api.post("/create_tag", tags=["Attributes - Tag"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def create_tag_endpoint(request, payload: CreateTagSchema):
    tag = create_tag(request, payload.name, payload.description)
    logger.info(f"create_tag endpoint succeeded for tag id={tag.id}")
    return 200, {
        "status": "success",
        "message": f"Tag created with id {tag.id}",
    }


@api.post("/create_and_add_tag_to_object", tags=["Attributes - Tag"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def create_and_add_tag_to_object_endpoint(request, payload: CreateTagObjectSchema):
    tag = create_and_add_tag_to_object(
        request, payload.name, payload.description, payload.object_type, payload.object_id
    )
    logger.info(
        f"create_and_add_tag_to_object endpoint succeeded for tag id={tag.id} and object id={payload.object_id}"
    )
    return 200, {
        "status": "success",
        "message": f"Tag created with id {tag.id} and added to object id={payload.object_id}",
    }


@api.delete("/clear_all_tags_from_object", tags=["Attributes - Tag"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def clear_all_tags_from_object_endpoint(request, object_id: int, object_type: str):
    deleted_count = clear_all_tags_from_object(object_id, object_type)
    logger.info(
        f"clear_all_tags_from_object endpoint succeeded for object id={object_id} and object type={object_type}. Deleted {deleted_count} tag connections."
    )
    return 200, {
        "status": "success",
        "message": f"Cleared all tags from object id={object_id} of type {object_type}. Deleted {deleted_count} tag connections.",
    }


@api.delete("/remove_tag_from_object", tags=["Attributes - Tag"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def remove_tag_from_object_endpoint(request, object_id: int, object_type: str, tag_id: int):
    deleted_count = remove_tag_from_object(object_id, object_type, tag_id)
    logger.info(
        f"remove_tag_from_object endpoint succeeded for tag id={tag_id} and object id={object_id} of type {object_type}. Deleted {deleted_count} tag connections."
    )
    return 200, {
        "status": "success",
        "message": f"Removed tag id={tag_id} from object id={object_id} of type {object_type}. Deleted {deleted_count} tag connections.",
    }


@api.delete("/delete_tag_from_tenant", tags=["Attributes - Tag"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def delete_tag_from_tenant_endpoint(request, tag_id: int):
    deleted_count = delete_tag_from_tenant(tag_id, request.session["current_tenant_id"])
    logger.info(
        f"delete_tag_from_tenant endpoint succeeded for tag id={tag_id} in tenant={request.session['current_tenant_id']}. Deleted {deleted_count} tag connections."
    )
    return 200, {
        "status": "success",
        "message": f"Deleted tag id={tag_id} from tenant. Deleted {deleted_count} tag connections.",
    }


"""
====================================================================
Management Objects
====================================================================
"""


@api.post("/create_tenant", tags=["Management - Tenant"], response={200: MessageSchema, 403: MessageSchema})
@require_superadmin
def create_tenant_endpoint(request, payload: CreateTenantSchema):
    tenant = create_tenant(request, payload.name)
    logger.info(f"create_tenant endpoint succeeded for tenant id={tenant.id}")
    return 200, {
        "message": "Tenant created",
        "status": f"Tenant created with id {tenant.id}",
    }


@api.get("/list_tenants", tags=["Management - Tenant"], response={200: list[dict], 403: MessageSchema})
@require_superadmin
def list_tenants(request):
    tenants = Tenant.objects.all()
    return 200, list(tenants.values())


@api.delete(
    "/delete_tenant",
    tags=["Management - Tenant"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_superadmin
def delete_tenant_endpoint(request, tenant_id: int):
    delete_tenant(tenant_id)
    logger.info(f"delete_tenant endpoint succeeded for tenant id={tenant_id}")
    return 200, {
        "status": "success",
        "message": f"Tenant with id {tenant_id}, name:  deleted.",
    }


@api.post("/create_device", tags=["Management - Device"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def create_device_endpoint(request, name: str, vendor: str, platform: str, model: str, role: str, description: str):
    device = create_device(
        request=request,
        name=name,
        vendor=vendor,
        platform=platform,
        model=model,
        role=role,
        description=description,
    )
    logger.info(f"create_device endpoint succeeded for device id={device.id}")
    return 200, {
        "message": "Device created",
        "status": f"Device created with id {device.id}",
    }


@api.post("/create_device_group", tags=["Management - Device"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def create_device_group_endpoint(request, payload: CreateAddressGroupSchema):
    device_group = create_device_group(
        request=request,
        name=payload.name,
        description=payload.description,
    )
    logger.info(f"create_device_group endpoint succeeded for device group id={device_group.id}")
    return 200, {
        "message": "Device Group created",
        "status": f"Device Group created with id {device_group.id}",
    }


@api.post("/add_devices_to_group", tags=["Management - Device"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def add_devices_to_group_endpoint(request, device_ids: list[int], group_id: int):
    response = add_devices_to_group(group_id, device_ids)

    logger.info(
        f"add_devices_to_group endpoint succeeded for device ids={response['added_device_ids']} and group id={group_id}"
    )

    return 200, {
        "status": "success",
        "message": (
            f"Processed device ids for group id={group_id}. "
            f"Added={response['added_device_ids']}, "
            f"already_present={response['already_present_device_ids']}, "
            f"not_found={response['not_found_device_ids']}"
        ),
    }


"""
====================================================================
Filter Objects
====================================================================
"""


@api.get("/list_rules", tags=["Filter - Rule"], response={200: list[dict], 403: MessageSchema})
@require_read_tenant
def list_rules(request):
    rules = get_all_rules_from_tenant(request.session["current_tenant_id"])
    return 200, list(rules.values())


@api.get("/list_rules_with_objects", tags=["Filter - Rule"], response={200: list[dict], 403: MessageSchema})
@require_read_tenant
def list_rules_with_objects(request):
    rules = get_all_rules_with_objects_from_tenant(request.session["current_tenant_id"])
    return 200, rules


@api.post("/create_rule", tags=["Filter - Rule"], response={200: MessageSchema, 403: MessageSchema})
@require_write_tenant
def create_rule_endpoint(request, payload: CreateRuleSchema):
    rule = create_rule(
        request=request,
        name=payload.name,
        description=payload.description,
        tenant_id=request.session["current_tenant_id"],
        action=payload.action,
        log_type=payload.log_type,
        hit_count=0,
        enable=payload.enable,
    )
    logger.info(f"create_rule endpoint succeeded for rule id={rule.id}")
    return 200, {
        "message": "Rule created",
        "status": f"Rule created with id {rule.id}",
    }


@api.post(
    "/add_object_to_rule",
    tags=["Filter - Rule"],
    response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema},
)
@require_write_tenant
def add_object_to_rule_endpoint(request, rule_id: int, match_type: str, object_type: str, object_ids: list[int]):
    try:
        objects = [DJANGO_MODEL_MAPPING[object_type].objects.get(id=obj_id) for obj_id in object_ids]
        result = add_objects_to_rule(request, rule_id, match_type, objects)
        logger.info(f"add_object_to_rule endpoint succeeded for rule id={rule_id}")
        return 200, {
            "status": "success",
            "message": str(result),
        }
    except ValueError as e:
        logger.warning(str(e))
        return 404, {
            "status": "error",
            "message": str(e),
        }


@api.delete(
    "/delete_rule", tags=["Filter - Rule"], response={200: MessageSchema, 403: MessageSchema, 404: MessageSchema}
)
@require_write_tenant
def delete_rule_endpoint(request, rule_id: int):
    try:
        delete_rule(rule_id, request.session["current_tenant_id"])
        logger.info(f"Rule deleted: id={rule_id}")
        return 200, {
            "status": "success",
            "message": f"Rule with id {rule_id} deleted.",
        }
    except ValueError as e:
        logger.warning(str(e))
        return 404, {
            "status": "error",
            "message": str(e),
        }


"""
====================================================================
User Management
====================================================================
"""


@api.post("/login", tags=["Authentication - User"], auth=None, response={200: MessageSchema})
def login_endpoint(request, payload: LoginSchema):
    user = authenticate(request, username=payload.username, password=payload.password)

    if user is None:
        logger.warning(f"Failed login attempt for username={payload.username}")
        return api.create_response(
            request,
            {"status": "error", "message": "Invalid username or password"},
            status=401,
        )

    login(request, user)
    logger.info(f"User logged in: {user.username}")

    if not user.is_superuser:
        if TenantUserMember.objects.filter(user_id=user.id).exists():
            request.session["current_tenant_id"] = TenantUserMember.objects.get(user_id=user.id).tenant_id

    return 200, {
        "status": "success",
        "message": "Logged in successfully",
        "username": user.username,
        "is_superuser": user.is_superuser,
        "session_key": request.session.session_key,
    }


@api.post("/logout", tags=["Authentication - User"])
def logout_endpoint(request):
    username = request.user.username if request.user.is_authenticated else "anonymous"
    logout(request)
    logger.info(f"User logged out: {username}")
    return {"status": "success", "message": "Logged out successfully"}


@api.get("/who_am_i", tags=["Authentication - User"], auth=None)
def who_am_i(request):
    if request.user.is_authenticated:
        return {
            "authenticated": True,
            "username": request.user.username,
            "email": request.user.email,
            "id": request.user.id,
            "current_tenant_id": request.session.get("current_tenant_id"),
        }

    return {
        "authenticated": False,
        "username": None,
        "email": None,
        "id": None,
    }


@api.get("/get_users", tags=["User Management"])
@require_superadmin
def get_users(request):
    return list(User.objects.values())


@api.post("/create_user", tags=["User Management"], auth=None)
@require_superadmin
def create_user(request, payload: CreateUserSchema):
    if User.objects.filter(username=payload.username).exists():
        return {
            "status": "error",
            "message": f"User with username '{payload.username}' already exists.",
        }

    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )

    logger.info(f"User created: {user.username}")
    return {
        "status": "success",
        "message": f"User '{payload.username}' created successfully.",
        "user_id": user.id,
    }


@api.delete("/delete_user", tags=["User Management"])
@require_superadmin
def delete_user(request, user_id: int):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        logger.info(f"User deleted: {user}")
        return {"status": "success", "message": f"User with id {user_id} deleted."}
    except User.DoesNotExist:
        logger.warning(f"Tried to delete user with id {user_id}, but it does not exist.")
        return {"status": "error", "message": f"User with id {user_id} does not exist."}


# This endpoint allows a superadmin to add a user to a tenant with a specific role. Only superadmins can perform this action.
@api.post(
    "/add_tenant_privileges_to_user",
    tags=["User Management - Tenant"],
    response={200: MessageSchema, 403: MessageSchema},
)
@require_superadmin
def add_tenant_privileges_to_user_endpoint(request, payload: CreateTenantUserSchema):
    if not is_superadmin(request.user):
        logger.warning(
            f"Unauthorized attempt to create TenantUserMember for tenant_id={payload.tenant_id} and user_id={payload.user_id}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to add users to this tenant.",
        }
    tenant_user = create_tenant_user_member(request, payload.tenant_id, payload.user_id, payload.role)
    logger.info(
        f"create_tenant_user endpoint succeeded for tenant_id={payload.tenant_id} and user_id={payload.user_id}"
    )
    return 200, {
        "status": "success",
        "message": f"Tenant User created: {tenant_user}",
    }
