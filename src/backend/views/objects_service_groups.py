from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger

from backend.views.modal import get_item_options_view

from backend.objects.attributes.service_group_member import ServiceGroupMember

from backend.services.attribute_objects.create_attribute_objects import create_service_group
from backend.services.attribute_objects.get_service_objects import get_service_group_members
from backend.services.membership import add_services_to_group, remove_service_from_group
from backend.services.update import update_service_group
from backend.services.delete import delete_service_group

logger = set_up_logger(__name__)

"""
====================================================================
Objects Page: Service Group
====================================================================
"""


# Handles creation of a new service group from modal form submission.
@login_required(login_url="login")
def post_service_group_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    service_ids = [int(service_id) for service_id in request.POST.getlist("service_ids") if service_id]

    try:
        created_service_group = create_service_group(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )

        if service_ids:
            add_services_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=created_service_group.id,
                service_ids=service_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "services",
                "modal_content_partial": "partials/modals/_service_group_form.html",
                "modal_supports_types": True,
                "modal_type": "group",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Service",
                    "group": "Service Group",
                },
                "error_message": f"Could not create service group: {e}",
                "item_options": get_item_options_view(request, "services"),
            },
            status=400,
        )

    row = {
        "id": f"servicegroup-{created_service_group.id}",
        "cells": [
            "ServiceGroup",
            created_service_group.name,
            created_service_group.description,
            "-",
            "-",
            "-",
            [],
        ],
        "raw": created_service_group,
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Handles updating an existing service group from modal form submission.
@login_required(login_url="login")
def update_service_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    service_ids = [int(service_id) for service_id in request.POST.getlist("service_ids") if service_id]

    object_data = {
        "name": name,
        "description": description,
        "services": [{"id": service_id} for service_id in service_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service Group",
                "modal_mode": "update",
                "modal_row_id": f"servicegroup-{object_id}",
                "modal_object_type": "services",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_group_form.html",
                "modal_post_url": reverse("update-service-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "services"),
                "selected_service_ids": service_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_service_group(
            actor=request.user,
            tenant_id=tenant_id,
            service_group_id=object_id,
            name=name,
            description=description,
        )

        # Read current members from the database
        current_members = get_service_group_members(
            actor=request.user,
            tenant_id=tenant_id,
            service_group_id=object_id,
        )

        current_service_ids = set(
            current_members.values_list("id", flat=True)
        )  # Convert current members to a set of ids
        submitted_service_ids = set(service_ids)  # Convert submitted selected ids to a set

        service_ids_to_remove = current_service_ids - submitted_service_ids  # Find what to remove
        service_ids_to_add = submitted_service_ids - current_service_ids  # Find what to add

        for service_id in service_ids_to_remove:
            remove_service_from_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=object_id,
                service_id=service_id,
            )

        if service_ids_to_add:
            add_services_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=object_id,
                service_ids=list(service_ids_to_add),
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service Group",
                "modal_mode": "update",
                "modal_row_id": f"servicegroup-{object_id}",
                "modal_object_type": "services",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_group_form.html",
                "modal_post_url": reverse("update-service-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "services"),
                "selected_service_ids": service_ids,
                "error_message": f"Could not update service group: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of a service group from the backend.
@login_required(login_url="login")
def delete_service_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_service_group(
            actor=request.user,
            tenant_id=tenant_id,
            service_group_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete service group: {e}", status=400)

    return HttpResponse(status=204)
