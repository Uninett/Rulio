from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.views.session import get_tenant_context

from backend.views.search import get_global_search_results

from backend.services.get import (
    get_all_filters_with_tags_from_tenant,
    get_filters_with_rules_with_tags_from_tenant,
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
            "object_extra_type": "rule",
            "add_button_label": "Add Filter",
            "add_extra_button_label": "Add Rule",
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

    tenant_id = int(tenant_id)

    try:
        _, filters, rules, tags = get_filters_with_rules_with_tags_from_tenant(
            request.user,
            tenant_id,
            include_global_tenant=True,
        )
    except Exception as e:
        print(f"Error fetching filters, rules, and tags: {e}")
        return {
            "headers": [],
            "rows": [],
        }

    filters = sorted(filters, key=lambda f: (getattr(f, "name", "") or "").lower())
    rules = sorted(rules, key=lambda r: (getattr(r, "name", "") or "").lower())

    headers = ["", "Name", "Description", "Rules", "Tags"]
    rows = []

    for filter_obj in filters:
        try:
            filter_tag_names = [tag.name for tag in filter_obj.get_tags()]
        except Exception:
            filter_tag_names = []

        try:
            filter_rule_names = [rule.name for rule in rules if rule.filter_id == filter_obj.id]
        except Exception:
            filter_rule_names = []

        rows.append(
            {
                "id": f"filter-{filter_obj.id}",
                "is_group": False,
                "cells": [
                    "▶",
                    getattr(filter_obj, "name", "") or "",
                    getattr(filter_obj, "description", "") or "",
                    ", ".join(filter_rule_names),
                    filter_tag_names,
                ],
                "expand": [
                    {
                        "label": "Rules",
                        "value": ", ".join(filter_rule_names),
                    },
                    {
                        "label": "Tags",
                        "value": filter_tag_names,
                    },
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
