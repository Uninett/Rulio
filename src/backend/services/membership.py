from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.address import Address
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


def add_address_to_group(request: object, address_group_id: int, address_id: int):
    _address_group = AddressGroup.objects.get(id=address_group_id)
    _address = Address.objects.get(id=address_id)
    _address_group_member = AddressGroupMember.objects.create(
        group_id=_address_group,
        address_id=_address,
    )


def get_address_group_members(request: object, address_group_id: int) -> list[Address]:
    return AddressGroupMember.objects.filter(address_group_id=address_group_id)
