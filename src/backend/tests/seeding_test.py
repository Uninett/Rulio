import pytest

from backend.objects.attributes.address import Address
from backend.objects.attributes.service import Service
from backend.services.seed.populate import populate_db
from constants import GLOBAL_TENNANT_ID


@pytest.mark.django_db
def test_populate_db_is_idempotent_for_seed_data():
    # Count the number of addresses and services before seeding
    address_count_before_seeding = Address.objects.filter(tenant_id=GLOBAL_TENNANT_ID).count()
    service_count_before_seeding = Service.objects.filter(tenant_id=GLOBAL_TENNANT_ID).count()

    # Seed the database
    default_address_count, default_service_count = populate_db()

    # Count the number of addresses and services after seeding
    address_count_after_first_seeding = Address.objects.filter(tenant_id=GLOBAL_TENNANT_ID).count()
    service_count_after_first_seeding = Service.objects.filter(tenant_id=GLOBAL_TENNANT_ID).count()

    # If new database
    if address_count_before_seeding == 0 and service_count_before_seeding == 0:
        # Check that the default counts were created and that they match the expected default counts
        assert address_count_after_first_seeding > 0
        assert service_count_after_first_seeding > 0
        assert address_count_after_first_seeding == default_address_count
        assert service_count_after_first_seeding == default_service_count

    # If database already had any global data
    else:
        assert address_count_after_first_seeding >= address_count_before_seeding
        assert service_count_after_first_seeding >= service_count_before_seeding

    # Seed the database again to check that duplicates are not created
    populate_db()

    address_count_after_second_seeding = Address.objects.filter(tenant_id=GLOBAL_TENNANT_ID).count()
    service_count_after_second_seeding = Service.objects.filter(tenant_id=GLOBAL_TENNANT_ID).count()

    # The counts should be the same as after the first seeding, confirming that no duplicates were created
    assert address_count_after_second_seeding == address_count_after_first_seeding
    assert service_count_after_second_seeding == service_count_after_first_seeding

    # Add test that deletes all global data and then seeds again to confirm that default data is re-created when missing?
