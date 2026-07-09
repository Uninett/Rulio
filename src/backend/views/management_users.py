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
            "table_data": get_users_view(request),
            **get_management_toolbar_context("users", add_button_label="Create User"),
        },
    )


def get_users_view(request):
    headers = ["Username", "", "Last login", "Date joined", "Actions"]
    rows = []

    for user in User.objects.all().order_by("username"):
        rows.append(
            {
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login,
                "date_joined": user.date_joined,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
