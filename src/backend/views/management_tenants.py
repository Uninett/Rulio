from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from backend.views.management_helpers import get_management_toolbar_context


@login_required(login_url="login")
def get_management_tenants(request):
    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "tenants"
    object_type = "tenants"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Tenant management",
            "object_type": object_type,
            "tenants_data": get_tenants_view(request),
            **get_management_toolbar_context("tenants", add_button_label="Create Tenant"),
        },
    )


def get_tenants_view(request):
    tenants = Tenant.objects.all().order_by("id")

    headers = ["Tenant", "Members", "Admins", "Actions"]
    rows = []

    for tenant in tenants:
        memberships = TenantUserMember.objects.filter(tenant=tenant).select_related("user").order_by("user__username")

        member_count = memberships.count()
        admin_count = memberships.filter(role=TenantUserMember.TenantRole.ADMIN).count()

        member_labels = [f"{membership.user.username} ({membership.role})" for membership in memberships]

        rows.append(
            {
                "id": tenant.id,
                "name": tenant.tenant_name,
                "member_count": member_count,
                "admin_count": admin_count,
                "members": member_labels,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
