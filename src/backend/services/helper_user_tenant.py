from backend.utils.logger import set_up_logger
from backend.objects.management.tenant_user_member import TenantUserMember


logger = set_up_logger(__name__)


def is_superadmin(user):
    return user.is_authenticated and user.is_superuser


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
