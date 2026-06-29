from datetime import datetime, timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.utils.logger import set_up_logger
from backend.services.get import get_current_tenant, get_current_tenant_id


logger = set_up_logger(__name__)


def create_rule(
    request: object,
    name: str,
    description: str,
    action: str,
    log_type: str,
    hit_count: int,
    enable: bool = True,
) -> Rule:
    tenant = get_current_tenant(request)
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
        created_by=request.user.id if hasattr(request, "user") else None,
        changed_by=request.user.id if hasattr(request, "user") else None,
        enable=enable,
    )
    try:
        rule.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Rule validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    rule.save()
    logger.info(f"Created {rule} for tenant={rule.tenant_id}")
    return rule


def create_filter(
    request: object,
    name: str,
    description: str,
) -> Filter:
    tenant_id = get_current_tenant_id(request)
    filter_obj = Filter(
        name=name,
        description=description,
        tenant_id=tenant_id,
    )
    try:
        filter_obj.full_clean()
    except DjangoValidationError as e:
        logger.warning(f"Filter validation failed: {e.message_dict}")
        raise ValueError(e.message_dict) from e

    filter_obj.save()
    logger.info(f"Created {filter_obj} for tenant={filter_obj.tenant_id}")
    return filter_obj
