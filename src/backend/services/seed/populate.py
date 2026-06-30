from django.db import transaction
from django.contrib.auth.models import User

from backend.objects.tenant_objects.tenant import Tenant
from backend.services.seed.seed_address_groups import seed_addressgroups
from backend.services.seed.seed_addresses import seed_addresses
from backend.services.seed.seed_service_groups import seed_servicegroups
from backend.services.seed.seed_services import seed_services
from constants import GLOBAL_TENANT_ID


@transaction.atomic
def populate_db(actor: User, tenant_id: int) -> tuple[int, int]:
    Tenant.objects.update_or_create(
        id=GLOBAL_TENANT_ID,
        defaults={"tenant_name": "Global Tenant"},
    )
    default_address_count = seed_addresses(actor, tenant_id)
    default_service_count = seed_services(actor, tenant_id)
    default_address_group_count = seed_addressgroups(actor, tenant_id)
    default_service_group_count = seed_servicegroups(actor, tenant_id)
    return default_address_count, default_service_count, default_address_group_count, default_service_group_count
