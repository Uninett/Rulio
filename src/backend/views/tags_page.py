from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from backend.utils.logger import set_up_logger

from backend.views.search import get_global_search_results
from backend.views.session import get_tenant_context

from backend.services.attribute_objects.create_attribute_objects import create_tag

from backend.services.get import (
    get_all_tags_from_tenant,
    get_all_objects_with_certain_tag,
)

from backend.services.update import (
    update_tag,
)

from backend.services.delete import (
    delete_tag_from_tenant,
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

    context = {
        "active_page": "tags",
        "page_title": "Tags",
        "title": "Tags",
        "object_type": "tags",
        "tags": get_tags_view(request),
        "add_button_label": "Add Tag",
        "search_results": get_global_search_results(request),
        **get_tenant_context(request),
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/_page_content.html", context)

    return render(request, "tags.html", context)


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

    headers = ["Name", "Description", ""]

    rows = []

    for item in tags:
        istrue = True
        results, objects = get_all_objects_with_certain_tag(
            actor=request.user, tenant_id=int(tenant_id), tag_id=item.id
        )
        logger.debug("Tag %s (%s)", item.id, item.name)
        for obj_type, obj_list in objects.items():
            logger.debug("View objects[%s] count = %s", obj_type, len(obj_list))
            if obj_type == "interface":
                logger.debug("Interface names = %s", [getattr(obj, "name", None) for obj in obj_list])
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


@login_required(login_url="login")
def post_tag_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    try:
        created_tag = create_tag(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "tags",
                "modal_content_partial": "partials/modals/_tag_form.html",
                "modal_supports_types": False,
                "object_data": {
                    "name": name,
                    "description": description,
                },
                "error_message": f"Could not create tag: {e}",
            },
            status=400,
        )

    row = {
        "id": f"tag-{created_tag.id}",
        "cells": [
            created_tag.name,
            created_tag.description,
        ],
        "raw": created_tag,
    }

    return render(
        request,
        "partials/objects/_tableRow.html",
        {
            "row": row,
            "headers": ["Name", "Description", ""],
            "object_type": "tags",
        },
    )


@login_required(login_url="login")
def update_tag_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")

    object_data = {
        "name": name,
        "description": description,
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Tag",
                "modal_mode": "update",
                "modal_row_id": f"tag-{object_id}",
                "modal_object_type": "tags",
                "modal_supports_types": False,
                "modal_content_partial": "partials/modals/_tag_form.html",
                "modal_post_url": reverse("update-tag-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_delete_url": reverse("delete-tag-view", args=[object_id]),
                "modal_refresh_url": reverse("tags"),
                "modal_refresh_target": "#tags-content",
                "object_data": object_data,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_tag(
            actor=request.user,
            tenant_id=tenant_id,
            tag_id=object_id,
            name=name,
            description=description,
        )
    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Tag",
                "modal_mode": "update",
                "modal_row_id": f"tag-{object_id}",
                "modal_object_type": "tags",
                "modal_supports_types": False,
                "modal_content_partial": "partials/modals/_tag_form.html",
                "modal_post_url": reverse("update-tag-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_delete_url": reverse("delete-tag-view", args=[object_id]),
                "modal_refresh_url": reverse("tags"),
                "modal_refresh_target": "#tags-content",
                "object_data": object_data,
                "error_message": f"Could not update tag: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


@login_required(login_url="login")
def delete_tag_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_tag_from_tenant(
            actor=request.user,
            tenant_id=tenant_id,
            tag_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete tag: {e}", status=400)

    return HttpResponse(status=204)
