from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from backend.services.filter_objects.create_filter_objects import create_filter
from backend.services.helper_user_tenant import can_write_tenant
from backend.services.membership import add_tag_to_object
from backend.services.update import update_filter
from backend.services.delete import delete_filter, remove_tag_from_object
from backend.views.session import get_tenant_context

from backend.objects.attributes.tag import Tag


from backend.views.search import get_global_search_results
from backend.services.get import (
    get_filters_with_rules_with_tags_from_tenant,
)
from constants import GLOBAL_TENANT_ID

from backend.services.get import get_all_tags_from_object

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
            "object_extra_type": "rules",
            "add_button_label": "Add Filter",
            "filters": get_filters_view(request),  # Address data for the page
            "search_results": get_global_search_results(request),
            **get_tenant_context(request),
        },
    )


@login_required(login_url="login")
def get_filters_content(request):
    request.session["active_page"] = "filters"

    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Filters",
            "page_title": "Filters",
            "object_type": "filters",
            "object_extra_type": "rules",
            "add_button_label": "Add Filter",
            "filters": get_filters_view(request),
            **get_tenant_context(request),
        },
    )


@login_required(login_url="login")
def delete_filter_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_filter(
            actor=request.user,
            tenant_id=tenant_id,
            filter_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete filter: {e}", status=400)

    return HttpResponse(status=204)


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
            filter_tags = get_all_tags_from_object(
                actor=request.user,
                tenant_id=int(tenant_id),
                object_type="filter",
                object_id=filter_obj.id,
            )
        except Exception:
            filter_tags = []

        try:
            filter_rule_names = [rule.name for rule in rules if rule.filter_id == filter_obj.id]
        except Exception:
            filter_rule_names = []

        rows.append(
            {
                "id": f"filter-{filter_obj.id}",
                "is_group": False,
                "inspect_url": reverse("rules-page") + f"?filter_id={filter_obj.id}&filter_name={filter_obj.name}",
                "is_global": filter_obj.tenant_id == GLOBAL_TENANT_ID,
                "can_write": can_write_tenant(request.user, filter_obj.tenant_id),
                "cells": [
                    "▶",
                    getattr(filter_obj, "name", "") or "",
                    getattr(filter_obj, "description", "") or "",
                    ", ".join(filter_rule_names),
                    filter_tags,
                ],
                "expand": [
                    {
                        "label": "Rules",
                        "value": ", ".join(filter_rule_names),
                    },
                    {
                        "label": "Tags",
                        "value": filter_tags,
                    },
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


@login_required(login_url="login")
def update_filter_view(request, object_id):
    name = request.POST.get("name")
    description = request.POST.get("description")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if tenant_id is None:
        return HttpResponse("No tenant selected.", status=400)

    try:
        updated_filter = update_filter(
            actor=request.user,
            tenant_id=tenant_id,
            filter_id=object_id,
            name=name,
            description=description,
        )

        submitted_tag_ids = {int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id}

        current_tags = get_all_tags_from_object(
            actor=request.user,
            tenant_id=tenant_id,
            object_id=object_id,
            object_type="filter",
        )
        current_tag_ids = {tag.id for tag in current_tags}

        tag_ids_to_add = submitted_tag_ids - current_tag_ids
        tag_ids_to_remove = current_tag_ids - submitted_tag_ids

        for tag_id in tag_ids_to_add:
            tag = Tag.objects.get(id=tag_id)

            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=updated_filter,
            )

        for tag_id in tag_ids_to_remove:
            remove_tag_from_object(
                actor=request.user,
                tenant_id=tenant_id,
                object_id=object_id,
                object_type="filter",
                tag_id=tag_id,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "filters",
                "modal_content_partial": "partials/modals/_filter_form.html",
                "modal_supports_types": False,
                "error_message": f"Could not update filter: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


@login_required(login_url="login")
def post_filter_view(request):
    name = request.POST.get("name")
    description = request.POST.get("description")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    try:
        created_filter = create_filter(
            actor=request.user,
            name=name,
            description=description,
            tenant_id=tenant_id,
        )

        submitted_tag_ids = {int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id}

        for tag_id in submitted_tag_ids:
            tag = Tag.objects.get(id=tag_id)

            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=created_filter,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "filters",
                "modal_content_partial": "partials/modals/_filter_form.html",
                "modal_supports_types": False,
                "error_message": f"Could not create filter: {e}",
            },
            status=400,
        )

    row = {
        "id": f"filter-{created_filter.id}",
        "cells": [
            "▶",
            getattr(created_filter, "name", "") or "",
            getattr(created_filter, "description", "") or "",
            "",
            [],
        ],
        "expand": [],
    }

    return render(
        request,
        "partials/objects/_tableRow.html",
        {
            "row": row,
        },
    )
