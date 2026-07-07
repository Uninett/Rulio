from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger

from backend.views.objects_helpers import get_objects_toolbar_context
from backend.views.modal import get_group_options_view

from backend.objects.attributes.service_group_member import ServiceGroupMember

from backend.services.attribute_objects.create_attribute_objects import (
    create_service,
)

from backend.services.membership import (
    add_service_to_group,
)

from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)

from backend.services.update import (
    update_service,
)

from backend.services.delete import (
    delete_service,
)

logger = set_up_logger(__name__)

"""
====================================================================
Objects Page: Service
====================================================================
"""


# Render the Services tab content for the Objects page.
@login_required(login_url="login")
def get_objects_services(request):
    request.session["active_page"] = "objects"
    return render(
        request,
        "partials/_page_content.html",
        {
            "title": "Services",
            "object_type": "services",
            "services": get_services_view(request),  # Service data for the page
            **get_objects_toolbar_context(
                "services", add_button_label="Add Service"
            ),  # Render the Objects page with Services as the active tab.
        },
    )


# Fetch services from the backend and map them to data.
def get_services_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {
            "headers": [],
            "rows": [],
        }

    try:
        services, _, _ = get_all_services_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
            include_global_tenant=False,
        )
    except Exception:
        return {
            "headers": [],
            "rows": [],
        }

    headers = ["Type", "Name", "Description", "Protocol", "Port Start", "Port End", "Tags"]

    rows = []

    for item in services:
        item_type = item.get("type", "")
        is_group = item_type == "ServiceGroup"

        tags_value = [tag.get("name", "") for tag in item.get("tags", [])]
        services_value = [service.get("name", "") for service in item.get("services", [])]

        if is_group:
            expand = [
                {"label": "Services", "value": services_value},
                {"label": "Tags", "value": tags_value},
            ]
        else:
            expand = [
                {
                    "label": "Tags",
                    "value": tags_value,
                },
            ]

        rows.append(
            {
                "id": f"{item.get('type', '').lower()}-{item.get('id')}",
                "is_group": is_group,
                "cells": [
                    "Group" if item.get("type") == "ServiceGroup" else item.get("type", ""),
                    item.get("name", ""),
                    item.get("description", ""),
                    item.get("protocol") or "",
                    item.get("port_start") or "",
                    item.get("port_end") or "",
                    tags_value,
                ],
                "expand": expand,
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


"""
====================================================================
Objects Page: Service Item
====================================================================
"""


# Handles creation of a new service from modal form submission.
@login_required(login_url="login")
def post_service_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    protocol = request.POST.get("protocol", "")
    port_start = int(request.POST.get("port_start")) if request.POST.get("port_start") else None
    port_end = int(request.POST.get("port_end")) if request.POST.get("port_end") else None
    group_ids = [int(group_id) for group_id in request.POST.getlist("group_ids") if group_id]

    try:
        created_service = create_service(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
            protocol=protocol,
            port_start=port_start,
            port_end=port_end,
        )

        for group_id in group_ids:
            add_service_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=group_id,
                service_id=created_service.id,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "services",
                "modal_content_partial": "partials/modals/_service_form.html",
                "modal_supports_types": True,
                "modal_type": "item",
                "item_type_editable": False,
                "modal_type_labels": {
                    "item": "Service",
                    "group": "Group",
                },
                "error_message": f"Could not create service: {e}",
                "group_options": get_group_options_view(request, "services"),
            },
            status=400,
        )

    row = {
        "id": f"service-{created_service.id}",
        "cells": [
            "Service",
            created_service.name,
            created_service.description,
            created_service.protocol,
            created_service.port_start or "",
            created_service.port_end or "",
            [],
        ],
        "raw": created_service,
    }

    return render(request, "partials/objects/_tableRow.html", {"row": row})


# Handles updating an existing service from modal form submission.
@login_required(login_url="login")
def update_service_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    protocol = request.POST.get("protocol", "")
    port_start = request.POST.get("port_start") or None
    port_end = request.POST.get("port_end") or None
    group_ids = [int(group_id) for group_id in request.POST.getlist("group_ids") if group_id]

    port_start = int(port_start) if port_start is not None else None
    port_end = int(port_end) if port_end is not None else None

    object_data = {
        "name": name,
        "description": description,
        "protocol": protocol,
        "port_start": port_start,
        "port_end": port_end,
        "service_groups": [{"id": group_id} for group_id in group_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service",
                "modal_mode": "update",
                "modal_row_id": f"service-{object_id}",
                "modal_object_type": "services",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_form.html",
                "modal_post_url": reverse("update-service-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "group_options": get_group_options_view(request, "services"),
                "selected_group_ids": group_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        updated_service = update_service(
            actor=request.user,
            tenant_id=tenant_id,
            service_id=object_id,
            name=name,
            description=description,
            protocol=protocol,
            port_start=port_start,
            port_end=port_end,
        )

        ServiceGroupMember.objects.filter(service_id=updated_service.id).delete()

        for group_id in group_ids:
            add_service_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                service_group_id=group_id,
                service_id=updated_service.id,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Service",
                "modal_mode": "update",
                "modal_row_id": f"service-{object_id}",
                "modal_object_type": "services",
                "modal_type": "item",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_service_form.html",
                "modal_post_url": reverse("update-service-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-services"),
                "object_data": object_data,
                "group_options": get_group_options_view(request, "services"),
                "selected_group_ids": group_ids,
                "error_message": f"Could not update service: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of a service from the backend.
@login_required(login_url="login")
def delete_service_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_service(
            actor=request.user,
            tenant_id=tenant_id,
            service_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete service: {e}", status=400)

    return HttpResponse(status=204)
