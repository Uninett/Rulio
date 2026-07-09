from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from backend.views.management_helpers import get_management_toolbar_context


def get_management_users_view(request):
    users = User.objects.all().order_by("username")

    rows = []
    for user in users:
        display_name = f"{user.first_name} {user.last_name}".strip() or user.username

        rows.append(
            {
                "id": user.id,
                "name": display_name,
                "username": user.username,
                "email": user.email,
            }
        )

    return rows


@login_required(login_url="login")
def get_management_users(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    request.session["active_page"] = "management"
    request.session["management_active_tool"] = "users"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "User management",
            "users_data": get_management_users_view(request),
            **get_management_toolbar_context("users"),
        },
    )
