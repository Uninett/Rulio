from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from backend.views.session import get_tenant_context
from backend.views.search import get_global_search_results
from backend.views.management_helpers import get_management_toolbar_context
from backend.views.management_users import get_users_view
from backend.views.management_tenants import get_tenants_view


"""
====================================================================
Management Page
====================================================================
"""


@login_required(login_url="login")
def get_management_page(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    request.session["active_page"] = "management"

    active_tool = request.GET.get("management_type") or request.session.get("management_active_tool", "users")

    if active_tool not in {"users", "tenants"}:
        active_tool = "users"

    request.session["management_active_tool"] = active_tool

    if active_tool == "tenants":
        page_title = "Tenant management"
        object_type = "tenants"
        content_context = {
            "tenants_data": get_tenants_view(request),
        }
        toolbar_context = get_management_toolbar_context("tenants", add_button_label="Create tenant")
    else:
        page_title = "User management"
        object_type = "users"
        content_context = {
            "users_data": get_users_view(request),
        }
        toolbar_context = get_management_toolbar_context("users", add_button_label="Create user")

    return render(
        request,
        "management.html",
        {
            "active_page": "management",
            "page_title": page_title,
            "object_type": object_type,
            "search_results": get_global_search_results(request),
            **toolbar_context,
            **content_context,
            **get_tenant_context(request),
        },
    )
