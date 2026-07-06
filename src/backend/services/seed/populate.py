from django.db import transaction
from django.contrib.auth.models import User

from backend.objects.tenant_objects.tenant import Tenant
from backend.services.seed.seed_address_groups import seed_addressgroups
from backend.services.seed.seed_addresses import seed_addresses
from backend.services.seed.seed_service_groups import seed_servicegroups
from backend.services.seed.seed_services import seed_services
from backend.services.seed.seed_rules import seed_rules
from backend.services.seed.seed_filters import seed_filters
from backend.services.seed.seed_tags import (
    add_tags_to_default_address_groups,
    seed_tags,
    add_tags_to_default_addresses,
    add_tags_to_default_services,
    add_tags_to_default_service_groups,
    add_tags_to_default_rules,
    add_tags_to_default_filters,
)
from constants import GLOBAL_TENANT_ID


@transaction.atomic
def populate_db(actor: User, tenant_id: int) -> tuple[int, int, int, int, int, int, int]:
    Tenant.objects.update_or_create(
        id=GLOBAL_TENANT_ID,
        defaults={"tenant_name": "Global Tenant"},
    )

    # Attribute objects to be seeded
    default_tag_count, _ = seed_tags(actor=actor, tenant_id=tenant_id)
    default_address_count, default_addresses = seed_addresses(actor=actor, tenant_id=tenant_id)
    add_tags_to_default_addresses(actor=actor, tenant_id=tenant_id, default_addresses=default_addresses)
    default_service_count, default_services = seed_services(actor=actor, tenant_id=tenant_id)
    add_tags_to_default_services(actor=actor, tenant_id=tenant_id, default_services=default_services)
    default_address_group_count, default_address_groups = seed_addressgroups(actor=actor, tenant_id=tenant_id)
    add_tags_to_default_address_groups(actor=actor, tenant_id=tenant_id, default_address_groups=default_address_groups)
    default_service_group_count, default_service_groups = seed_servicegroups(actor=actor, tenant_id=tenant_id)
    add_tags_to_default_service_groups(actor=actor, tenant_id=tenant_id, default_service_groups=default_service_groups)

    default_filter_count, default_filters = seed_filters(actor=actor, tenant_id=tenant_id)
    add_tags_to_default_filters(actor=actor, tenant_id=tenant_id, default_filters=default_filters)

    # Filter objects to be seeded
    default_rules_count, default_rules = seed_rules(
        actor=actor,
        tenant_id=tenant_id,
        seeded_addresses=default_addresses,
        seeded_address_groups=default_address_groups,
        seeded_services=default_services,
        seeded_service_groups=default_service_groups,
        seeded_filters=default_filters
    )
    add_tags_to_default_rules(actor=actor, tenant_id=tenant_id, default_rules=default_rules)

    return (
        default_tag_count,
        default_address_count,
        default_service_count,
        default_address_group_count,
        default_service_group_count,
        default_rules_count,
        default_filter_count,
    )
