

from django.contrib.auth.models import User
from ninja import NinjaAPI

from backend.services.create import create_address, create_service
from backend.schemas.address import CreateAddressSchema
from backend.schemas.group import CreateGroupSchema
from backend.schemas.tag import CreateTagSchema
from backend.schemas.tag_object import CreateTagObjectSchema
from backend.schemas.service import CreateServiceSchema
from .objects.all_objects import Address, AddressGroup, ServiceGroup, Tag, TagObject
from backend.utils.logger import set_up_logger, add_file_handler
from constants import LOGPATH, ERROR_LOGPATH

api = NinjaAPI()

#Logger setup
logger = set_up_logger(__name__)


"""
====================================================================
Tests
====================================================================
"""


@api.get("/hello", tags=["Debugging"])
def hello(request):
    return "Hello world"

#This is a temporary endpoint to set the tenant ID in the session for testing purposes. In a real implementation, this would be handled by an authentication system and middleware.
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
def create_address_api(request, payload: CreateAddressSchema):
    address = create_address(request, payload.name, payload.description, payload.ipv4Address, payload.ipv6Address, payload.type)
    logger.info(f"create_address endpoint succeeded for address id={address.id}")
    return f"Address created: {address}"

@api.post("/create_service", tags=["Attributes"])
def create_service_api(request, payload: CreateServiceSchema):
    service = create_service(request, payload.name, payload.description, payload.protocol, payload.port_start, payload.port_end)
    logger.info(f"create_service endpoint succeeded for service id={service.id}")
    return f"Service created: {service}"

@api.post("/create_service_group", tags=["Attributes"])
def create_service_group(request, payload: CreateGroupSchema):
    service_group = ServiceGroup() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Service Group created: {service_group}")
    return f"Service Group created {service_group}"

@api.post("/create_address_group", tags=["Attributes"])
def create_address_group(request, payload: CreateGroupSchema):
    address_group = AddressGroup() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Address Group created: {address_group}")
    return f"Address Group created {address_group}"

@api.post("/create_tag", tags=["Attributes"])
def create_tag(request, payload: CreateTagSchema):
    tag = Tag() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Tag created: {tag}")
    return f"Tag created {tag}"

@api.post("/create_tag_object", tags=["Attributes"])
def create_tag_object(request, payload: CreateTagObjectSchema):
    tag_object = TagObject() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    logger.info(f"Tag Object created: {tag_object}")
    return f"Tag Object created {tag_object}"

@api.post("/add_address_to_group", tags=["Attributes"])
def add_address_to_group(request, address_id: int, group_id: int):
    # This is a placeholder function to demonstrate the endpoint. The actual implementation would involve database operations to add the address to the group.
    logger.info(f"Address {address_id} added to group {group_id}")
    return f"Address {address_id} added to group {group_id}"

@api.post("/add_service_to_group", tags=["Attributes"])
def add_service_to_group(request, service_id: int, group_id: int):
    # This is a placeholder function to demonstrate the endpoint. The actual implementation would involve database operations to add the service to the group.
    logger.info(f"Service {service_id} added to group {group_id}")
    return f"Service {service_id} added to group {group_id}"



"""
====================================================================
User Management
====================================================================
"""


@api.get("/members", tags=["User Management"])
def members(request):
    return list(User.objects.values())

@api.post("/create_user", tags=["User Management"])
def create_user(request, username: str, email: str, password: str):
    if User.objects.filter(username=username).exists():
        return {"status": "error", "message": f"User with username '{username}' already exists."}
    
    user = User.objects.create_user(username=username, email=email, password=password)
    logger.info(f"User created: {user}")
    return {"status": "success", "message": f"User '{username}' created successfully.", "user_id": user.id}

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
    
@api.post("/add_address")
def add_address(request, name: str, description: str, tenant_id: int, type: str, ipv4_value: str = None, ipv6_value: str = None):
    address = Address.objects.create(
        name=name,
        description=description,
        tenant_id=tenant_id,
        type=type,
        ipv4_value=ipv4_value,
        ipv6_value=ipv6_value
    )
    return {"status": "success", "message": f"Address '{name}' created successfully.", "address_id": address.id}

@api.get("/list_addresses")
def list_addresses(request):
    addresses = Address.objects.all()
    return list(addresses.values())

