from datetime import datetime, timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.models import User

from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.utils.logger import set_up_logger
from backend.services.helper_user_tenant import get_tenant_by_id, require_write_tenant


logger = set_up_logger(__name__)


def create_rule(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    action: str,
    log_type: str,
    hit_count: int,
) -> Rule:
    require_write_tenant(actor, tenant_id)
    tenant = get_tenant_by_id(tenant_id)
    now = datetime.now(timezone.utc)
    rule = Rule(
        name=name,
        description=description,
        tenant=tenant,
        action=action,
        log_type=log_type,
        hit_count=hit_count,
        date_created=now,
        date_changed=now,
        created_by=actor.id,
        changed_by=actor.id,
    )
    try:
        rule.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Rule validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    rule.save()
    logger.info(f"Created {rule} for tenant={rule.tenant_id}")
    return rule


def get_or_create_rule(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
    action: str,
    log_type: str,
    hit_count: int,
) -> tuple[Rule, bool]:
    require_write_tenant(actor, tenant_id)
    rule, created = Rule.objects.get_or_create(
        tenant_id=tenant_id,
        name=name,
        defaults={
            "description": description,
            "action": action,
            "log_type": log_type,
            "hit_count": hit_count,
            "date_created": datetime.now(timezone.utc),
            "date_changed": datetime.now(timezone.utc),
            "created_by": actor.id,
            "changed_by": actor.id,
        },
    )
    if created:
        rule.full_clean()
        logger.info(f"Created {rule} for tenant={rule.tenant_id}")
    else:
        logger.info(f"Found existing {rule} for tenant={rule.tenant_id}")
    return rule, created


def create_filter(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
) -> Filter:
    require_write_tenant(actor, tenant_id)
    tenant = get_tenant_by_id(tenant_id)
    filter_obj = Filter(
        name=name,
        description=description,
        tenant=tenant,
    )
    try:
        filter_obj.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Filter validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    filter_obj.save()
    logger.info(f"Created {filter_obj} for tenant={filter_obj.tenant_id}")
    return filter_obj


def get_or_create_filter(
    *,
    actor: User,
    tenant_id: int,
    name: str,
    description: str,
) -> tuple[Filter, bool]:
    require_write_tenant(actor, tenant_id)
    filter_obj, created = Filter.objects.get_or_create(
        tenant_id=tenant_id,
        name=name,
        defaults={
            "description": description,
        },
    )
    if created:
        filter_obj.full_clean()
        logger.info(f"Created {filter_obj} for tenant={filter_obj.tenant_id}")
    else:
        logger.info(f"Found existing {filter_obj} for tenant={filter_obj.tenant_id}")
    return filter_obj, created
