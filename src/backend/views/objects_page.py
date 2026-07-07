from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from backend.utils.logger import set_up_logger

from backend.views.search import get_search_view
from backend.views.session import get_tenant_context
from backend.views.objects_helpers import get_objects_toolbar_context
from backend.views.objects_addresses import get_addresses_view
from backend.views.objects_services import get_services_view

logger = set_up_logger(__name__)


"""
====================================================================
Objects Page
====================================================================
"""


@login_required(login_url="login")
def get_objects_page(request):
    request.session["active_page"] = "objects"
    active_tool = request.session.get("objects_active_tool", "addresses")

    if active_tool == "services":
        page_title = "Services"
        object_type = "services"
        content_context = {
            "services": get_services_view(request),
        }
        toolbar_context = get_objects_toolbar_context("services", add_button_label="Add Service")
    else:
        page_title = "Addresses"
        object_type = "addresses"
        content_context = {
            "addresses": get_addresses_view(request),
        }
        toolbar_context = get_objects_toolbar_context("addresses", add_button_label="Add Address")

    return render(
        request,
        "objects.html",
        {
            "active_page": "objects",
            "page_title": page_title,
            "object_type": object_type,
            **toolbar_context,  # Render the Objects page with Addresses as the default tab.
            **content_context,  # Address data for the page
            "page_title": "Addresses",
            "object_type": "addresses",
            **get_objects_toolbar_context("addresses"),  # Render the Objects page with Addresses as the default tab.
            "addresses": get_addresses_view(request),  # Address data for the page
            "search_results": get_search_view(request),
            **get_tenant_context(request),
        },
    )
