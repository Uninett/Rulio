
import ipaddress

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

def get_current_tenant_id(request: object) -> int:
    if hasattr(request, 'current_tenant_id'):
        return request.current_tenant_id
    else:
        raise Exception("Tenant ID not set in request. Please set tenant using /set_tenant endpoint before creating objects.")

def create_address(request: object, name: str, description: str, ipv4Address: str, ipv6Address: str, type: str) -> Address:
    id = get_next_id()
    tenant_id = get_current_tenant_id(request)
    ipv4_addr = ipaddress.IPv4Address(ipv4Address)
    ipv6_addr = ipaddress.IPv6Address(ipv6Address)
    address = Address(
        id=id,
        name=name,
        description=description,
        tenant_id=tenant_id,
        type=type,
        ipv4_value=ipv4_addr,
        ipv6_value=ipv6_addr
    )
    # Save the address to the database here
    return address