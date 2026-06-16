from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.address import Address
from backend.objects.management.tenant import Tenant
from backend.objects.management.tenant_user_member import TenantUserMember
from backend.services.helper_user_tenant import can_write_tenant, get_tenant_membership
from backend.schemas import address, address_group
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


def add_address_to_group(request: object, address_group_id: int, address_id: int):
    address_group = AddressGroup.objects.get(id=address_group_id)
    address = Address.objects.get(id=address_id)
    address_group_member = AddressGroupMember.objects.create(
        group_id=address_group,
        address_id=address,
    )



def get_address_group_members(request: object, address_group_id: int) -> list[Address]:
    return AddressGroupMember.objects.filter(address_group_id=address_group_id)
