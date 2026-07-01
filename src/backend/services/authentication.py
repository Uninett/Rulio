from functools import wraps

from ninja import Status
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.helper_user_tenant import (
    is_superadmin,
    can_write_tenant,
    can_read_tenant,
)


def require_write_tenantd(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant_id = request.session.get("current_tenant_id")
        if tenant_id is None:
            return Status(403, {
                "status": "error",
                "message": "No tenant selected.",
            })

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Status(403, {
                "status": "error",
                "message": "Tenant does not exist.",
            })

        if not can_write_tenant(request.user, tenant):
            return Status(403, {
                "status": "error",
                "message": "You do not have permission to modify this tenant.",
            })
        return view_func(request, *args, **kwargs)

    return wrapper


def require_read_tenantd(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant_id = request.session.get("current_tenant_id")
        if tenant_id is None:
            return Status(403, {
                "status": "error",
                "message": "No tenant selected.",
            })

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Status(403, {
                "status": "error",
                "message": "Tenant does not exist.",
            })

        if not can_read_tenant(request.user, tenant):
            return Status(403, {
                "status": "error",
                "message": "You do not have permission to access this tenant.",
            })
        return view_func(request, *args, **kwargs)

    return wrapper


def require_superadmind(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_superadmin(request.user):
            return Status(403, {
                "status": "error",
                "message": "You do not have permission to perform this action.",
            })
        return view_func(request, *args, **kwargs)

    return wrapper
