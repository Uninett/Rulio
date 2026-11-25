from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from backend.services.helper_user_tenant import can_write_tenant
from backend.views.session import get_tenant_context
from constants import GLOBAL_TENANT_ID
from backend.services.get_unused_objects import get_unused_objects


@login_required(login_url="/login/")
def get_tools_page(request):
    request.session["active_page"] = "tools"
    context = {
        "page_title": "Tools",
        **get_tenant_context(request),
    }

    return render(request, "tools.html", context)


@login_required(login_url="/login/")
def get_unused_objects_page(request):
    request.session["active_page"] = "tools"
    context = {
        "active_page": "tools",
        "title": "Unused Objects",
        "page_title": "Unused Objects",
        "object_type": "unused_objects",
        "unused_objects": get_unused_objects_view(request),
        **get_tenant_context(request),
    }

    return render(request, "tools.html", context)


@login_required(login_url="/login/")
def get_unused_objects_view(request):
    URL_CONFIG = {
        "address": f"{reverse('objects')}?object_type=addresses",
        "addressgroup": f"{reverse('objects')}?object_type=addressgroups",
        "service": f"{reverse('objects')}?object_type=services",
        "servicegroup": f"{reverse('objects')}?object_type=servicegroups",
        "tag": f"{reverse('tags')}?object_type=tags",
        "filter": f"{reverse('filters')}?object_type=filters",
    }
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    groups = zip(
        ["address", "addressgroup", "service", "servicegroup", "tag", "filter"],
        get_unused_objects(request.user, tenant_id),
    )

    rows = []
    for prefix, queryset in groups:
        for obj in queryset:
            rows.append(
                {
                    "id": f"{prefix}-{obj.id}",
                    "is_global": obj.tenant_id == GLOBAL_TENANT_ID,
                    "can_write": can_write_tenant(request.user, obj.tenant_id),
                    "cells": [type(obj).__name__, obj.name],
                    "redirect_url": URL_CONFIG.get(prefix) + f"&expand_id={prefix}-{obj.id}",
                }
            )

    return {"headers": ["Type", "Name", ""], "rows": rows}
