from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from backend.views.session import get_tenant_context


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

    return render(
        request,
        "management.html",
        {
            "active_page": "management",
            "page_title": "Management",
            **get_tenant_context(request),
        },
    )
