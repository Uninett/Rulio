from backend.utils.logger import set_up_logger
from backend.objects.management.tenant_user_member import TenantUserMember
from django.contrib.auth.models import User


logger = set_up_logger(__name__)

def verify_user_access_to_tenant(request, user_id: str, tenant_id: str) -> bool:
    if not request.user.is_authenticated:
        logger.warning("Access denied: unauthenticated user")
        return False

    if request.user.is_superuser:
        return True

    allowed = (
        request.user.id == int(user_id)
        and str(request.session.get("current_tenant_id")) == str(tenant_id)
        and TenantUserMember.objects.filter(tenant_id=tenant_id, user_id=user_id).exists()
    )

    if not allowed:
        logger.warning(
            f"Access denied for request.user.id={request.user.id}, tenant_id={tenant_id}, user_id={user_id}"
        )

    return allowed