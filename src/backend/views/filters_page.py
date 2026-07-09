from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.views.session import get_tenant_context

from backend.views.search import get_global_search_results

from backend.services.get import (
    get_all_filters_with_tags_from_tenant,
)

"""
====================================================================
Filters Page
====================================================================
"""


@login_required(login_url="login")
def get_filters_page(request):
    request.session["active_page"] = "filters"
    return render(
        request,
        "filters.html",
        {
            "active_page": "filters",
            "page_title": "Filters",
            "object_type": "filters",
            "add_button_label": "Add Filter",
            "filters": get_filters_view(request),  # Address data for the page
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )


def get_filters_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        results, filters = get_all_filters_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = [
        "Name",
        "Description",
    ]

    rows = []

    for item in results:
        expand = [
            {"label": "Filter Name", "value": item.get("filter_name", "")},
            {"label": "Filter Description", "value": item.get("filter_description", "")},
            {"label": "Direction", "value": item.get("direction", "")},
            {"label": "Enable", "value": item.get("enable", "")},
        ]

        rows.append(
            {
                "id": item.get("filter_id", ""),
                "cells": [
                    item.get("filter_name", ""),
                    item.get("filter_description", ""),
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
