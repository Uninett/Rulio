from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from backend.views.management_helpers import get_management_toolbar_context
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember


@login_required(login_url="login")
def get_management_users(request):
    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "users"
    object_type = "users"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "User management",
            "object_type": object_type,
            "users_data": get_users_view(request),
            **get_management_toolbar_context("users", add_button_label="Create User"),
        },
    )


def get_users_view(request):
    users = User.objects.all().order_by("username")

    headers = ["Name", "Username", "Email", "Memberships", "Actions"]
    rows = []

    for user in users:
        display_name = f"{user.first_name} {user.last_name}".strip() or user.username

        memberships = TenantUserMember.objects.filter(user=user).select_related("tenant").order_by("tenant__id")

        membership_labels = [f"{membership.tenant.tenant_name} ({membership.role})" for membership in memberships]

        rows.append(
            {
                "id": user.id,
                "name": display_name,
                "username": user.username,
                "email": user.email,
                "memberships": membership_labels,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
