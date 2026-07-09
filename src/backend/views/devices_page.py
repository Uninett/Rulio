from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.views.session import get_tenant_context

from backend.views.search import get_global_search_results

"""
====================================================================
Device Page
====================================================================
"""


@login_required(login_url="login")
def get_devices_page(request):
    request.session["active_page"] = "devices"
    return render(
        request,
        "devices.html",
        {
            "active_page": "devices",
            "page_title": "Devices",
            "object_type": "devices",
            "add_button_label": "Add Device",
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )
