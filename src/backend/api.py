from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from ninja import NinjaAPI, Schema
from ninja.security import django_auth
from django.conf import settings

from backend.objects.management.tenant_user_member import TenantUserMember
from backend.schemas.address_group import CreateAddressGroupSchema
from backend.schemas.tenant_user import CreateTenantUserSchema
from backend.services.create import (
    create_address,
    create_service,
    create_tenant_user_member,
    create_tenant,
    create_address_group,
)
from backend.schemas.address import CreateAddressSchema
from backend.schemas.group import CreateGroupSchema
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
from backend.objects.attributes.tag_object import TagObject
from backend.services.helper_user_tenant import (
    is_superadmin,
    can_write_tenant,
    get_tenant_membership,
)
from backend.services.membership import add_address_to_group
from backend.utils.logger import set_up_logger

#Frontend
from django.shortcuts import render

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


@api.post("/create_address", tags=["Attributes"])
def create_address_endpoint(request, payload: CreateAddressSchema):
    address = create_address(
        request=request,
        name=payload.name,
        description=payload.description,
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
    return {
        "message": "Address created",
        "address_id": address.id,
        "name": address.name,
        "status": "success",
    }



@api.post("/create_service", tags=["Attributes"])
def create_service_endpoint(request, payload: CreateServiceSchema):
    service = create_service(
        request,
        payload.name,
        payload.description,
        payload.protocol,
        payload.port_start,
        payload.port_end,
    )
    logger.info(f"create_service endpoint succeeded for service id={service.id}")
    return {
        "message": "Service created",
        "service_id": service.id,
        "name": service.name,
    }


@api.post("/create_tenant", tags=["Attributes"])
def create_tenant_endpoint(request, payload: CreateTenantSchema):
    tenant = create_tenant(request, payload.name)
    logger.info(f"create_tenant endpoint succeeded for tenant id={tenant.id}")
    return f"Tenant created: {tenant}"


@api.post(
    "/add_tenant_privileges_to_user",
    tags=["Attributes"],
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
    tenant_user = create_tenant_user_member(
        request, payload.tenant_id, payload.user_id, payload.role
    )
    logger.info(
        f"create_tenant_user endpoint succeeded for tenant_id={payload.tenant_id} and user_id={payload.user_id}"
    )
    return 200, {
        "status": "success",
        "message": f"Tenant User created: {tenant_user}",
    }


@api.post("/create_service_group", tags=["Attributes"])
def create_service_group_endpoint(request, payload: CreateGroupSchema):
    service_group = ServiceGroup()  # Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Service Group created: {service_group}")
    return f"Service Group created {service_group}"


@api.post(
    "/create_address_group",
    tags=["Attributes"],
    response={200: MessageSchema, 403: MessageSchema},
)
def create_address_group_endpoint(request, payload: CreateAddressGroupSchema):
    if not can_write_tenant(request.user, Tenant.objects.get(id=payload.tenant_id)):
        logger.warning(
            f"Unauthorized attempt to create address group with name={payload.name} for tenant_id={payload.tenant_id} by user {request.user.username}"
        )
        return 403, {
            "status": "error",
            "message": "You do not have permission to create an address group for this tenant.",
        }
    address_group = create_address_group(
        request, payload.name, payload.description, payload.tenant_id
    )
    logger.info(
        f"create_address_group endpoint succeeded for group id={address_group.id}"
    )
    return 200, {
        "status": "success",
        "message": f"Address Group created: {address_group}",
    }


@api.post("/create_tag", tags=["Attributes"])
def create_tag_endpoint(request, payload: CreateTagSchema):
    tag = Tag()  # Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Tag created: {tag}")
    return f"Tag created {tag}"


@api.post("/create_tag_object", tags=["Attributes"])
def create_tag_object_endpoint(request, payload: CreateTagObjectSchema):
    tag_object = TagObject()  # Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Tag Object created: {tag_object}")
    return f"Tag Object created {tag_object}"


@api.post(
    "/add_address_to_group",
    tags=["Attributes"],
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
    address_group = add_address_to_group(request, group_id, address_id)
    logger.info(
        f"add_address_to_group endpoint succeeded for address id={address_id} and group id={group_id}"
    )
    return 200, {
        "status": "success",
        "message": f"Address id={address_id} added to group id={group_id}",
    }


@api.post("/add_service_to_group", tags=["Attributes"])
def add_service_to_group_endpoint(request, service_id: int, group_id: int):
    # This is a placeholder function to demonstrate the endpoint. The actual implementation would involve database operations to add the service to the group.
    logger.info(f"Service {service_id} added to group {group_id}")
    return f"Service {service_id} added to group {group_id}"




@api.get("/list_addresses")
def list_addresses(request):
    addresses = Address.objects.all()
    return list(addresses.values())


"""
====================================================================
User Management
====================================================================
"""


@api.post("/login", tags=["Authentication"], auth=None, response={200: MessageSchema})
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
            request.session["current_tenant_id"] = TenantUserMember.objects.get(
                user_id=user.id
            ).tenant_id

    return 200, {
        "status": "success",
        "message": "Logged in successfully",
        "username": user.username,
        "is_superuser": user.is_superuser,
        "session_key": request.session.session_key,
    }


@api.post("/logout", tags=["Authentication"])
def logout_endpoint(request):
    username = request.user.username if request.user.is_authenticated else "anonymous"
    logout(request)
    logger.info(f"User logged out: {username}")
    return {"status": "success", "message": "Logged out successfully"}


@api.get("/who_am_i", tags=["Authentication"], auth=None)
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
        logger.warning(
            f"Tried to delete user with id {user_id}, but it does not exist."
        )
        return {"status": "error", "message": f"User with id {user_id} does not exist."}


@api.post("/add_address")
def add_address(
    request,
    name: str,
    description: str,
    tenant_id: int,
    type: str,
    ipv4_value: str = None,
    ipv6_value: str = None,
):
    address = Address.objects.create(
        name=name,
        description=description,
        tenant_id=tenant_id,
        type=type,
        ipv4_value=ipv4_value,
        ipv6_value=ipv6_value,
    )
    return {
        "status": "success",
        "message": f"Address '{name}' created successfully.",
        "address_id": address.id,
    }


@api.get("/list_addresses")
def list_addresses(request):
    addresses = Address.objects.all()
    return list(addresses.values())


"""
Frontend
"""
def devices(request):
    return render(request, "devices.html", {
        "active_page": "devices",
    })

def filters(request):
    return render(request, "filters.html", {
        "active_page": "filters",
    })

def objects(request):
    return render(request, "objects.html", {
        "active_page": "objects",
    })

def tags(request):
    return render(request, "tags.html", {
        "active_page": "tags",
    })
