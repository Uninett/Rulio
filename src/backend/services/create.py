from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from backend.utils.logger import set_up_logger
from backend.services.helper_user_tenant import is_superadmin

from backend.objects.tenant_objects.tenant_user_member import TenantUserMember


# Setup logger
logger = set_up_logger(__name__)


def create_tenant_user_member(
    *,
    actor: User,
    tenant_id: int,
    user_id: int,
    role: str,
) -> TenantUserMember:
    if not actor.is_authenticated:
        raise PermissionDenied("Authentication required.")

    if not is_superadmin(actor):
        raise PermissionDenied("Only superadmins can add tenant privileges to users.")

    tenant_user = TenantUserMember.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
    )
    logger.info(f"TenantUserMember created by {actor.username}: {tenant_user}")
    return tenant_user
