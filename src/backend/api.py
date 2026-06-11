from ninja import NinjaAPI

from backend.services.create import create_address, create_service
from backend.schemas.address import CreateAddressSchema
from backend.schemas.service import CreateServiceSchema
from backend.objects import *

api = NinjaAPI()


""""
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
    return {"message": f"Tenant set to {tenant_id}"}



""""
====================================================================
ATTRIBUTES
====================================================================
"""


@api.post("/create_address", tags=["Attributes"])
def create_address_api(request, payload: CreateAddressSchema):
    address = create_address(request, payload.name, payload.description, payload.ipv4Address, payload.ipv6Address, payload.type)
    return f"Address created: {address}"

@api.post("/create_service", tags=["Attributes"])
def create_service_api(request, payload: CreateServiceSchema):
    service = create_service(request, payload.name, payload.description, payload.protocol, payload.port_start, payload.port_end)
    return f"Service created: {service}"

@api.post("/create_service_group", tags=["Attributes"])
def create_service_group(request, name: str, description: str):
    service_group = ServiceGroup() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    return f"Service Group created {service_group}"

@api.post("/create_address_group", tags=["Attributes"])
def create_address_group(request, name: str, description: str):
    address_group = AddressGroup() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    return f"Address Group created {address_group}"

@api.post("/create_tag", tags=["Attributes"])
def create_tag(request, name: str, description: str):
    tag = Tag() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    return f"Tag created {tag}"

@api.post("/create_tag_object", tags=["Attributes"])
def create_tag_object(request, tag_id: int, object_type: str, object_id: int):
    tag_object = TagObject() #Do this properly when we have the model set up, this is just a placeholder to get the endpoint working for now
    return f"Tag Object created {tag_object}"

@api.post("/add_address_to_group", tags=["Attributes"])
def add_address_to_group(request, address_id: int, group_id: int):
    # This is a placeholder function to demonstrate the endpoint. The actual implementation would involve database operations to add the address to the group.
    return f"Address {address_id} added to group {group_id}"

@api.post("/add_service_to_group", tags=["Attributes"])
def add_service_to_group(request, service_id: int, group_id: int):
    # This is a placeholder function to demonstrate the endpoint. The actual implementation would involve database operations to add the service to the group.
    return f"Service {service_id} added to group {group_id}"