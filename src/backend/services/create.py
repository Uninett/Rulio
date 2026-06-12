
import ipaddress



from backend.objects.all_objects import Address, Service
from backend.utils.logger import set_up_logger



#Setup logger
logger = set_up_logger(__name__)


#Temp solution for ID generation
current_id = 1
def get_next_id() -> int:
    # Placeholder function to get the next available ID
    # In a real implementation, this would query the database or use a sequence
    global current_id
    next_id = current_id + 1
    current_id = next_id
    return next_id


# This is a temporary solution for tenant ID management. In a real implementation, this would be handled by an authentication system and middleware that sets the tenant ID in the request context.
def get_current_tenant_id(request: object) -> int:
    tenant_id = request.session.get("current_tenant_id")
    if tenant_id is None:
        logger.warning("Tenant ID not set in request session.")
        raise Exception(
            "Tenant ID not set in request. Please call /set_tenant first."
        )
    try:
        return int(tenant_id)
    except ValueError:
        logger.warning(f"Invalid tenant ID in session: {tenant_id}")
        raise Exception(f"Invalid tenant ID in session: {tenant_id}")



""""
====================================================================
ATTRIBUTES
====================================================================
"""


def create_address(request: object, name: str, description: str, ipv4Address: str, ipv6Address: str, addr_type: str) -> Address:
    
    id = get_next_id()
    tenant_id = get_current_tenant_id(request)
    # These try-except blocks are redundant since the Pydantic schema should already validate the IP addresses, 
    # not sure if we should keep them or not 
    try:
        ipv4_addr = ipaddress.IPv4Network(ipv4Address)
    except ipaddress.AddressValueError as e:
        logger.warning(f"Tried to create address with invalid IPv4 address: {ipv4Address}")
        raise ValueError(f"Invalid IPv4 address: {ipv4Address}") from e
        
    try:
        ipv6_addr = ipaddress.IPv6Network(ipv6Address)
    except ipaddress.AddressValueError as e:
        logger.warning(f"Tried to create address with invalid IPv6 address: {ipv6Address}")
        raise ValueError(f"Invalid IPv6 address: {ipv6Address}") from e
    
    address = Address(
        id=id,
        name=name,
        description=description,
        tenant_id=tenant_id,
        type=addr_type,
        ipv4_value=ipv4_addr,
        ipv6_value=ipv6_addr
    )
    # Save the address to the database here
    logger.info(f"Created {address} for tenant={address.tenant_id}")
    return address

def create_service(request: object, name: str, description: str, protocol: str, port_start: int, port_end: int) -> Service:
    
    addr_id = get_next_id()
    tenant_id = get_current_tenant_id(request)

    service = Service(
        id=addr_id,
        name=name,
        description=description,
        tenant_id=tenant_id,
        protocol=protocol,
        port_start=port_start,
        port_end=port_end
    )
    # Save the service to the database here
    logger.info(f"Created {service} for tenant={service.tenant_id}")
    return service