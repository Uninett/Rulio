from django.core.exceptions import PermissionDenied

from backend.objects.tenant_objects.tenant import Tenant
from backend.utils.logger import set_up_logger
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember


logger = set_up_logger(__name__)


def get_current_tenant_id(request: object) -> int:
    tenant_id = request.session.get("current_tenant_id")
    if tenant_id is None:
        logger.warning("Tenant ID not set in request session.")
        raise PermissionDenied("Tenant ID not set in request. Please call /set_tenant first.")
    try:
        return int(tenant_id)
    except ValueError:
        logger.warning(f"Invalid tenant ID in session: {tenant_id}")
        raise PermissionDenied(f"Invalid tenant ID in session: {tenant_id}")


def get_tenant_by_id(tenant_id: int) -> Tenant:
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        return tenant
    except Tenant.DoesNotExist:
        logger.warning(f"Tenant with ID {tenant_id} does not exist.")
        raise PermissionDenied(f"Tenant with ID {tenant_id} does not exist.")


def get_current_tenant(request: object) -> Tenant:
    tenant_id = get_current_tenant_id(request)
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        return tenant
    except Tenant.DoesNotExist:
        logger.warning(f"Tenant with ID {tenant_id} does not exist.")
        raise PermissionDenied(f"Tenant with ID {tenant_id} does not exist.")


def require_current_tenant(request: object) -> Tenant:
    tenant = get_current_tenant(request)
    if tenant is None:
        raise PermissionDenied("Current tenant not set or does not exist.")
    return tenant


def is_superadmin(user):
    return user.is_authenticated and user.is_superuser


def require_superadmin(user):
    if not is_superadmin(user):
        raise PermissionDenied("Superadmin privileges required.")


def get_tenant_membership(user, tenant):
    if not user.is_authenticated:
        return None
    return TenantUserMember.objects.filter(user=user, tenant=tenant).first()


def is_tenant_admin(user, tenant):
    if is_superadmin(user):
        return True

    membership = get_tenant_membership(user, tenant)
    return membership is not None and membership.role == TenantUserMember.TenantRole.ADMIN


def can_read_tenant(user, tenant):
    if is_superadmin(user):
        return True

    membership = get_tenant_membership(user, tenant)
    return membership is not None


def can_write_tenant(user, tenant):
    return is_tenant_admin(user, tenant)


def is_authenticated_user(user):
    return bool(user and user.is_authenticated)


def require_authenticated_user(user):
    if not is_authenticated_user(user):
        raise PermissionDenied("Authentication required.")
    return user


def require_read_tenant(user, tenant_id):
    require_authenticated_user(user)
    if tenant_id is None:
        raise PermissionDenied("No tenant selected.")
    if not can_read_tenant(user, tenant_id):
        raise PermissionDenied(f"You do not have permission to read tenant {tenant_id}.")


def require_write_tenant(user, tenant_id):
    require_authenticated_user(user)
    if tenant_id is None:
        raise PermissionDenied("No tenant selected.")
    if not can_write_tenant(user, tenant_id):
        raise PermissionDenied(f"You do not have permission to modify tenant {tenant_id}.")
