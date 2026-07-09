from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from backend.views.management_helpers import get_management_toolbar_context


def get_management_tenants_view(request):
    tenants = Tenant.objects.all().order_by("id")

    rows = []
    for tenant in tenants:
        member_count = TenantUserMember.objects.filter(tenant=tenant).count()

        rows.append(
            {
                "id": tenant.id,
                "name": tenant.tenant_name,
                "member_count": member_count,
            }
        )

    return rows


@login_required(login_url="login")
def get_management_tenants(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "tenants"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Tenant management",
            "tenants_data": get_management_tenants_view(request),
            **get_management_toolbar_context("tenants"),
        },
    )
