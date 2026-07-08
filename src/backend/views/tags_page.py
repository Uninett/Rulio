from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from backend.utils.logger import set_up_logger

from backend.views.search import get_global_search_results
from backend.views.session import get_tenant_context

from backend.services.get import (
    get_all_tags_from_tenant,
    get_all_objects_with_certain_tag,
)

logger = set_up_logger(__name__)

"""
====================================================================
Tags Page
====================================================================
"""


@login_required(login_url="login")
def get_tags_page(request):
    request.session["active_page"] = "tags"
    return render(
        request,
        "tags.html",
        {
            "active_page": "tags",
            "page_title": "Tags",
            "object_type": "tags",
            "add_button_label": "Add Tag",
            "tags": get_tags_view(request),
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )


# Fetch services from the API and map them to data.
def get_tags_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        tags = get_all_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Name", "Description"]

    rows = []

    for item in tags:
        istrue = True
        results, objects = get_all_objects_with_certain_tag(
            actor=request.user, tenant_id=int(tenant_id), tag_id=item.id
        )
        logger.info("Tag %s (%s)", item.id, item.name)
        for obj_type, obj_list in objects.items():
            logger.info("View objects[%s] count = %s", obj_type, len(obj_list))
            if obj_type == "interface":
                logger.info("Interface names = %s", [getattr(obj, "name", None) for obj in obj_list])
        expand = [
            {"label": "Addresses", "value": [obj.name for obj in objects["address"]], "special_style": True},
            {"label": "Address Group", "value": [obj.name for obj in objects["addressgroup"]], "special_style": True},
            {"label": "Services", "value": [obj.name for obj in objects["service"]], "special_style": True},
            {"label": "Service Group", "value": [obj.name for obj in objects["servicegroup"]], "special_style": True},
            {"label": "Rule", "value": [obj.name for obj in objects["rule"]], "special_style": True},
            {"label": "Filter", "value": [obj.name for obj in objects["filter"]], "special_style": True},
            {"label": "Device", "value": [obj.name for obj in objects["device"]], "special_style": True},
            {"label": "Interface", "value": [obj.name for obj in objects["interface"]], "special_style": True},
        ]

        rows.append(
            {
                "id": f"tag-{item.id}",
                "istrue": istrue,
                "cells": [
                    item.name,
                    item.description,
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
