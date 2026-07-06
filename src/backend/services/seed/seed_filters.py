from django.contrib.auth.models import User

from backend.objects.filters.filter import Filter
from backend.services.filter_objects.create_filter_objects import get_or_create_filter

from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def seed_filters(
    *,
    actor: User,
    tenant_id: int,
) -> tuple[int, list[Filter]]:
    default_filters = []

    filter_1, created_1 = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Baseline_Internal_Client_Policy",
        description="Baseline internal client policy allowing common business traffic and denying risky categories.",
    )

    default_filters.append((filter_1, created_1))

    filter_2, created_2 = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Internal_Server_Policy",
        description="Internal server policy allowing management, identity, database, file sharing, and monitoring services for private networks.",
    )

    default_filters.append((filter_2, created_2))

    filter_3, created_3 = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Strict_Egress_Policy",
        description="Strict egress policy for private address space allowing only core infrastructure and web access while denying common risky categories.",
    )

    default_filters.append((filter_3, created_3))

    created_flags = [filter_obj[1] for filter_obj in default_filters]
    default_filter_count = len(default_filters)
    default_filters = [filter_obj[0] for filter_obj in default_filters]

    if all(created_flags):
        logger.info("All default filters were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default filters already existed. Missing filters were created.")
    else:
        logger.warning("No default filters were created because they already all existed.")

    return default_filter_count, default_filters
