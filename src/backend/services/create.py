
from backend.objects import *

#Temp solution for ID generation
current_id = 1
def get_next_id() -> int:
    # Placeholder function to get the next available ID
    # In a real implementation, this would query the database or use a sequence
    global current_id
    next_id = current_id + 1
    current_id = next_id
    return next_id

def get_current_tenant_id(request) -> int:
    if hasattr(request, 'current_tenant_id'):
        return request.current_tenant_id
    else:
        raise Exception("Tenant ID not set in request. Please set tenant using /set_tenant endpoint before creating objects.")

def create_address(request, name: str, description: str, ipv4Address: str, ipv6Address: str, type: str) -> Address:
    id = get_next_id()
    tenant_id = get_current_tenant_id(request)
    address = Address(
        id=id,
        name=name,
        description=description,
        tenant_id=tenant_id,
        type=type,
        ipv4Address=ipv4Address,
        ipv6Address=ipv6Address,
        type=type
    )
    # Save the address to the database here
    return address