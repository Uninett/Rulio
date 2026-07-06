from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from backend.utils.logger import set_up_logger

from backend.views.session import get_tenant_context
from backend.views.objects_helpers import get_objects_toolbar_context
from backend.views.objects_addresses import get_addresses_view

logger = set_up_logger(__name__)


"""
====================================================================
Objects Page
====================================================================
"""


@login_required(login_url="login")
def get_objects_page(request):
    request.session["active_page"] = "objects"
    return render(
        request,
        "objects.html",
        {
            "active_page": "objects",
            "page_title": "Addresses",
            "object_type": "addresses",
            **get_objects_toolbar_context("addresses"),  # Render the Objects page with Addresses as the default tab.
            "addresses": get_addresses_view(request),  # Address data for the page
            **get_tenant_context(request),
        },
    )
