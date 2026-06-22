from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from ninja import NinjaAPI
from ninja.security import django_auth
from django.conf import settings

from backend.objects.attributes.service import Service
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.schemas.address_group import CreateAddressGroupSchema
from backend.schemas.tenant_user import CreateTenantUserSchema
from backend.services.get import (
    get_all_tags_from_object,
    get_service_groups_with_services_from_tenant,
    get_address_groups_with_addresses_from_tenant,
)
from backend.services.create import (
    add_services_to_group,
    create_address,
    create_and_add_tag_to_object,
    create_service,
    create_tenant_user_member,
    create_tenant,
    create_address_group,
    get_current_tenant_id,
    create_service_group,
    add_service_to_group,
    add_addresses_to_group,
)
from backend.schemas.address import CreateAddressSchema
from backend.schemas.tag import CreateTagSchema
from backend.schemas.tag_object import CreateTagObjectSchema
from backend.schemas.service import CreateServiceSchema
from backend.schemas.login import LoginSchema
from backend.schemas.create_user import CreateUserSchema
from backend.schemas.tenant import CreateTenantSchema
from backend.schemas.message import MessageSchema
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.tag import Tag
from backend.objects.management.tenant import Tenant
from backend.services.helper_user_tenant import (
    is_superadmin,
    can_write_tenant,
    can_read_tenant,
)
from backend.services.membership import add_address_to_group
from backend.utils.logger import set_up_logger


api = NinjaAPI()

# Logger setup
logger = set_up_logger(__name__)


api = NinjaAPI(auth=None if settings.DEBUG else django_auth)


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


@api.post(
    "/create_address",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema},
)
def create_address_endpoint(
    request,
    payload: CreateAddressSchema,
):
    if can_write_tenant(request.user, Tenant.objects.get(id=get_current_tenant_id(request))) is False:
        logger.warning(
            f"Unauthorized attempt to create service with name={payload.name} for tenant_id={get_current_tenant_id(request)} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to create a service for this tenant.",
        }
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
    "/create_service",
    tags=["Attributes - Service"],
    response={200: MessageSchema, 403: MessageSchema},
)
def create_service_endpoint(
    request,
    payload: CreateServiceSchema,
):
    if can_write_tenant(request.user, Tenant.objects.get(id=get_current_tenant_id(request))) is False:
        logger.warning(
            f"Unauthorized attempt to create service with name={payload.name} for tenant_id={get_current_tenant_id(request)} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to create a service for this tenant.",
        }
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
def create_service_group_endpoint(request, payload: CreateAddressGroupSchema):
    if not can_write_tenant(request.user, Tenant.objects.get(id=payload.tenant_id)):
        logger.warning(
            f"Unauthorized attempt to create service group with name={payload.name} for tenant_id={payload.tenant_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to create a service group for this tenant.",
        }
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


@api.post(
    "/create_address_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema},
)
def create_address_group_endpoint(request, payload: CreateAddressGroupSchema):
    tenant_id = request.session.get("current_tenant_id")
    if not can_write_tenant(request.user, Tenant.objects.get(id=tenant_id)):
        logger.warning(
            f"Unauthorized attempt to create address group with name={payload.name} for tenant_id={tenant_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to create an address group for this tenant.",
        }
    address_group = create_address_group(request, payload.name, payload.description, tenant_id)
    logger.info(f"create_address_group endpoint succeeded for group id={address_group.id}")
    return 200, {
        "status": "success",
        "message": f"Address Group created: {address_group}",
    }


@api.post("/create_tag", tags=["Attributes - Tag"])
def create_tag_endpoint(request, payload: CreateTagSchema):
    tag = Tag()
    # Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Tag created: {tag}")
    return f"Tag created {tag}"


@api.post("/create_tag_object", tags=["Attributes - Tag"])
def create_tag_object_endpoint(request, payload: CreateTagObjectSchema):
    tag_object = TagObject()
    # Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Tag Object created: {tag_object}")
    return f"Tag Object created {tag_object}"


@api.post(
    "/add_address_to_group",
    tags=["Attributes - Address"],
    response={200: MessageSchema, 403: MessageSchema},
)
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
            f"Unauthorized attempt to add services id={address_ids} "
            f"to group id={group_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to modify this service group.",
        }

    response = add_addresses_to_group(group_id, address_ids)

    logger.info(
        f"add_addresses_to_group endpoint succeeded for "
        f"service ids={response['added_addresses_ids']} and group id={group_id}"
    )

    return 200, {
        "status": "success",
        "message": (
            f"Processed address ids for group id={group_id}. "
            f"Added={response['added_addresses_ids']}, "
            f"already_present={response['already_present_address_ids']}, "
            f"not_found={response['not_found_address_ids']}"
        ),
    }


@api.get(
    "/get_service_group_and_services",
    tags=["Attributes - Service"],
    response={200: list[dict], 403: MessageSchema},
)
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
    "/get_address_group_and_addresses",
    tags=["Attributes - Address"],
    response={200: list[dict], 403: MessageSchema},
)
def get_address_group_and_addresses_endpoint(request, get="all"):
    if not can_read_tenant(request.user, request.session["current_tenant_id"]):
        logger.warning(
            f"Unauthorized attempt to read addresses from tenant={request.session['current_tenant_id']} "
            f"by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to read addresses from this tenant.",
        }
    response = get_address_groups_with_addresses_from_tenant(
        request.session["current_tenant_id"],
        get=get,
    )
    return 200, response


@api.get("/list_services", tags=["Attributes - Service"], response={200: list[dict], 403: MessageSchema})
def list_services(request):
    if not can_read_tenant(request.user, request.session["current_tenant_id"]):
        logger.warning(
            f"Unauthorized attempt to read services from tenant={request.session['current_tenant_id']} "
            f"by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to read services from this tenant.",
        }
    services = Service.objects.filter(tenant_id=request.session["current_tenant_id"])
    return 200, list(services.values())


@api.get("/list_addresses", tags=["Attributes - Address"], response={200: list[dict], 403: MessageSchema})
def list_addresses(request):
    if not can_read_tenant(request.user, request.session["current_tenant_id"]):
        logger.warning(
            f"Unauthorized attempt to read addresses from tenant={request.session['current_tenant_id']} "
            f"by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to read addresses from this tenant.",
        }
    addresses = Address.objects.filter(tenant_id=request.session["current_tenant_id"])
    return 200, list(addresses.values())


@api.post("/create_and_add_tag_to_object", tags=["Attributes - Tag"], response={200: MessageSchema, 403: MessageSchema})
def create_and_add_tag_to_object_endpoint(request, payload: CreateTagObjectSchema):
    if not can_write_tenant(request.user, Tenant.objects.get(id=request.session["current_tenant_id"])):
        logger.warning(
            f"Unauthorized attempt to create tag with name={payload.name} for tenant_id={request.session['current_tenant_id']} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to create a tag for this tenant.",
        }
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


@api.get("/get_all_tags_from_object", tags=["Attributes - Tag"], response={200: list[dict], 403: MessageSchema})
def get_all_tags_from_object_endpoint(request, object_id: int, object_type: str):
    if not can_read_tenant(request.user, request.session["current_tenant_id"]):
        logger.warning(
            f"Unauthorized attempt to read tags from tenant={request.session['current_tenant_id']} "
            f"by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to read tags from this tenant.",
        }
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


"""
====================================================================
Management Objects
====================================================================
"""


@api.post("/create_tenant", tags=["Management - Tenant"], response={200: MessageSchema, 403: MessageSchema})
def create_tenant_endpoint(request, payload: CreateTenantSchema):
    tenant = create_tenant(request, payload.name)
    logger.info(f"create_tenant endpoint succeeded for tenant id={tenant.id}")
    return 200, {
        "message": "Tenant created",
        "status": f"Tenant created with id {tenant.id}",
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


@api.get("/members", tags=["User Management"])
def members(request):
    return list(User.objects.values())


@api.post("/create_user", tags=["User Management"], auth=None)
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
