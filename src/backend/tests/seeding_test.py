import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
from backend.services.seed.populate import populate_db
from constants import GLOBAL_TENANT_ID


def get_seed_counts():
    return (
        Address.objects.filter(tenant_id=GLOBAL_TENANT_ID).count(),
        Service.objects.filter(tenant_id=GLOBAL_TENANT_ID).count(),
        AddressGroup.objects.filter(tenant_id=GLOBAL_TENANT_ID).count(),
        ServiceGroup.objects.filter(tenant_id=GLOBAL_TENANT_ID).count(),
    )


@pytest.mark.django_db
def test_populate_db_creates_seed_data():
    address_count_before_seeding, service_count_before_seeding, address_group_count_before_seeding, service_group_count_before_seeding = get_seed_counts()

    default_address_count, default_service_count, default_address_group_count, default_service_group_count = populate_db()

    address_count_after_seeding, service_count_after_seeding, address_group_count_after_seeding, service_group_count_after_seeding = get_seed_counts()

    if (
        address_count_before_seeding == 0
        and service_count_before_seeding == 0
        and address_group_count_before_seeding == 0
        and service_group_count_before_seeding == 0
    ):
        assert address_count_after_seeding > 0
        assert service_count_after_seeding > 0
        assert address_group_count_after_seeding > 0
        assert service_group_count_after_seeding > 0

        assert address_count_after_seeding == default_address_count
        assert service_count_after_seeding == default_service_count
        assert address_group_count_after_seeding == default_address_group_count
        assert service_group_count_after_seeding == default_service_group_count
    else:
        assert address_count_after_seeding >= address_count_before_seeding
        assert service_count_after_seeding >= service_count_before_seeding
        assert address_group_count_after_seeding >= address_group_count_before_seeding
        assert service_group_count_after_seeding >= service_group_count_before_seeding


@pytest.mark.django_db
def test_populate_db_does_not_create_duplicate_seed_data():
    populate_db()

    address_count_after_first_seeding, service_count_after_first_seeding, address_group_count_after_first_seeding, service_group_count_after_first_seeding = get_seed_counts()

    populate_db()

    address_count_after_second_seeding, service_count_after_second_seeding, address_group_count_after_second_seeding, service_group_count_after_second_seeding = get_seed_counts()

    assert address_count_after_second_seeding == address_count_after_first_seeding
    assert service_count_after_second_seeding == service_count_after_first_seeding
    assert address_group_count_after_second_seeding == address_group_count_after_first_seeding
    assert service_group_count_after_second_seeding == service_group_count_after_first_seeding


@pytest.mark.django_db
def test_populate_db_recreates_missing_seed_data():
    default_address_count, default_service_count, default_address_group_count, default_service_group_count = populate_db()

    AddressGroup.objects.filter(tenant_id=GLOBAL_TENANT_ID).delete()
    ServiceGroup.objects.filter(tenant_id=GLOBAL_TENANT_ID).delete()
    Address.objects.filter(tenant_id=GLOBAL_TENANT_ID).delete()
    Service.objects.filter(tenant_id=GLOBAL_TENANT_ID).delete()

    populate_db()

    address_count_after_reseeding, service_count_after_reseeding, address_group_count_after_reseeding, service_group_count_after_reseeding = get_seed_counts()

    assert address_count_after_reseeding == default_address_count
    assert service_count_after_reseeding == default_service_count
    assert address_group_count_after_reseeding == default_address_group_count
    assert service_group_count_after_reseeding == default_service_group_count