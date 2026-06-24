from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.address_group_member import AddressGroupMember
from backend.objects.attributes.address import Address
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.objects.attributes.service_group_member import ServiceGroupMember
from django.db import transaction
from backend.utils.logger import set_up_logger

logger = set_up_logger(__name__)


def add_address_to_group(request: object, address_group_id: int, address_id: int):
    _address_group = AddressGroup.objects.get(id=address_group_id)
    _address = Address.objects.get(id=address_id)
    _address_group_member = AddressGroupMember.objects.create(
        group=_address_group,
        address=_address,
    )


def add_service_to_group(request: object, service_group_id: int, service_id: int) -> ServiceGroup:
    _service_group = ServiceGroup.objects.get(id=service_group_id)
    _service = Service.objects.get(id=service_id)
    _service_group_member = ServiceGroupMember.objects.create(
        group=_service_group,
        service=_service,
    )


def add_addresses_to_group(address_group_id: int, address_ids: list[int]) -> dict:
    address_group = AddressGroup.objects.get(id=address_group_id)

    request_ids = set(address_ids)

    existing_addresses = Address.objects.filter(id__in=request_ids)
    found_ids = {address.id for address in existing_addresses}
    not_found_ids = request_ids - found_ids
    already_present_ids = set(
        AddressGroupMember.objects.filter(
            group=address_group,
            address__in=found_ids,
        ).values_list("address_id", flat=True)
    )

    new_addresses = [address for address in existing_addresses if address.id not in already_present_ids]

    with transaction.atomic():
        AddressGroupMember.objects.bulk_create(
            [AddressGroupMember(group=address_group, address=address) for address in new_addresses]
        )
    added_ids = [address.id for address in new_addresses]

    logger.info(
        f"Group {address_group.id}: added={added_ids}, "
        f"already_present={list(already_present_ids)}, "
        f"not_found={list(not_found_ids)}"
    )

    return {
        "address_group_id": address_group.id,
        "added_address_ids": sorted(added_ids),
        "already_present_address_ids": sorted(already_present_ids),
        "not_found_address_ids": sorted(not_found_ids),
    }


def add_services_to_group(service_group_id: int, service_ids: list[int]) -> dict:
    """
    Adds a list of services to a service group
    Args:
    - service_group_id: ID of the service group to add services to
    - service_ids: List of service IDs to add to the group
    """
    service_group = ServiceGroup.objects.get(id=service_group_id)

    requested_ids = set(service_ids)

    existing_services = Service.objects.filter(id__in=requested_ids)
    found_ids = {service.id for service in existing_services}
    not_found_ids = requested_ids - found_ids

    already_present_ids = set(
        ServiceGroupMember.objects.filter(
            group=service_group,
            service_id__in=found_ids,
        ).values_list("service_id", flat=True)
    )

    new_services = [service for service in existing_services if service.id not in already_present_ids]

    with transaction.atomic():
        ServiceGroupMember.objects.bulk_create(
            [ServiceGroupMember(group=service_group, service=service) for service in new_services]
        )

    added_ids = [service.id for service in new_services]

    logger.info(
        f"Group {service_group.id}: added={added_ids}, "
        f"already_present={list(already_present_ids)}, "
        f"not_found={list(not_found_ids)}"
    )

    return {
        "service_group_id": service_group.id,
        "added_service_ids": sorted(added_ids),
        "already_present_service_ids": sorted(already_present_ids),
        "not_found_service_ids": sorted(not_found_ids),
    }
