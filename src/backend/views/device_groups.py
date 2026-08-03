from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger

from backend.views.modal import get_item_options_view

from backend.services.tenant_objects.create_tenant_objects import create_device_group
from backend.services.membership import add_devices_to_group

from backend.services.membership import add_tag_to_object
from backend.objects.attributes.tag import Tag

logger = set_up_logger(__name__)


"""
====================================================================
Objects Page: device Group
====================================================================
"""


# Handles creation of a new device group from modal form submission.
@login_required(login_url="login")
def post_device_group_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    device_ids = [int(device_id) for device_id in request.POST.getlist("device_ids") if device_id]

    try:
        created_device_group = create_device_group(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )

        if device_ids:
            add_devices_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                device_group_id=created_device_group.id,
                device_ids=device_ids,
            )

        submitted_tag_ids = [int(tag_id) for tag_id in request.POST.getlist("tag_ids") if tag_id]

        for tag_id in submitted_tag_ids:
            tag = Tag.objects.get(id=tag_id)
            add_tag_to_object(
                actor=request.user,
                tenant_id=tenant_id,
                tag=tag,
                obj=created_device_group,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "devices",
                "modal_content_partial": "partials/modals/_device_group_form.html",
                "modal_supports_types": True,
                "modal_type": "group",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "device",
                    "group": "device Group",
                },
                "error_message": f"Could not create device group: {e}",
                "item_options": get_item_options_view(request, "devices"),
            },
            status=400,
        )

    row = {
        "id": f"devicegroup-{created_device_group.id}",
        "cells": [
            "deviceGroup",
            created_device_group.name,
            created_device_group.description,
            "-",
            "-",
            [],
        ],
        "expand": [
            "",
            "",
            "",
            "",
            "",
            "",
            [],
            [],
        ],
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})
