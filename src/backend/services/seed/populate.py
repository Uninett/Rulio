from django.db import transaction

from backend.services.seed.seed_address_groups import seed_addressgroups
from backend.services.seed.seed_addresses import seed_addresses
from backend.services.seed.seed_service_groups import seed_servicegroups
from backend.services.seed.seed_services import seed_services


@transaction.atomic
def populate_db() -> tuple[int, int]:
    default_address_count = seed_addresses()
    default_service_count = seed_services()
    default_address_group_count = seed_addressgroups()
    default_service_group_count = seed_servicegroups()
    return default_address_count, default_service_count, default_address_group_count, default_service_group_count
