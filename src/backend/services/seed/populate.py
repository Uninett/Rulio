from django.db import transaction

from backend.objects.management.tenant import Tenant
from backend.services.seed.seed_address_groups import seed_addressgroups
from backend.services.seed.seed_addresses import seed_addresses
from backend.services.seed.seed_service_groups import seed_servicegroups
from backend.services.seed.seed_services import seed_services
from constants import GLOBAL_TENANT_ID


@transaction.atomic
def populate_db() -> tuple[int, int]:
    Tenant.objects.update_or_create(
        id=GLOBAL_TENANT_ID,
        defaults={"tenant_name": "Global Tenant"},
    )
    default_address_count = seed_addresses()
    default_service_count = seed_services()
    default_address_group_count = seed_addressgroups()
    default_service_group_count = seed_servicegroups()
    return default_address_count, default_service_count, default_address_group_count, default_service_group_count
