from django.db import transaction

from backend.services.seed.seed_addresses import seed_addresses
from backend.services.seed.seed_services import seed_services


@transaction.atomic
def populate_db() -> tuple[int, int]:
    default_address_count = seed_addresses()
    default_service_count = seed_services()
    return default_address_count, default_service_count
