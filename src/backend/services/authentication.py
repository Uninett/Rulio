from functools import wraps
from backend.objects.management.tenant import Tenant
from backend.services.helper_user_tenant import (
    is_superadmin,
    can_write_tenant,
    can_read_tenant,
)


def require_write_tenant(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant_id = request.session.get("current_tenant_id")
        if tenant_id is None:
            return 403, {
                "status": "error",
                "message": "No tenant selected.",
            }

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return 403, {
                "status": "error",
                "message": "Tenant does not exist.",
            }

        if not can_write_tenant(request.user, tenant):
            return 403, {
                "status": "error",
                "message": "You do not have permission to modify this tenant.",
            }
        return view_func(request, *args, **kwargs)

    return wrapper


def require_read_tenant(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant_id = request.session.get("current_tenant_id")
        if tenant_id is None:
            return 403, {
                "status": "error",
                "message": "No tenant selected.",
            }

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return 403, {
                "status": "error",
                "message": "Tenant does not exist.",
            }

        if not can_read_tenant(request.user, tenant):
            return 403, {
                "status": "error",
                "message": "You do not have permission to access this tenant.",
            }
        return view_func(request, *args, **kwargs)

    return wrapper


def require_superadmin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_superadmin(request.user):
            return 403, {
                "status": "error",
                "message": "You do not have permission to perform this action.",
            }
        return view_func(request, *args, **kwargs)

    return wrapper
