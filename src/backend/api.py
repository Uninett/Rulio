from ninja import NinjaAPI

from backend.services.create import create_address
from backend.objects import *

api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return "Hello world"


@api.get("/set_tenant")
def set_tenant(request, tenant_id: str):
    request.current_tenant_id = tenant_id
    return f"Tenant set to {tenant_id}"


@api.get("/create_address")
def create_address(request, name: str, description: str, ipv4Address: str, ipv6Address: str, type: str):
    address = create_address(request, name, description, ipv4Address, ipv6Address, type)
    return f"Address created: {address}"
