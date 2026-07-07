from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from backend.utils.logger import set_up_logger

from backend.views.modal import get_item_options_view

from backend.objects.attributes.address_group_member import AddressGroupMember

from backend.services.attribute_objects.create_attribute_objects import (
    create_address_group,
)

from backend.services.membership import (
    add_addresses_to_group,
)

from backend.services.update import (
    update_address_group,
)

from backend.services.delete import (
    delete_address_group,
)

logger = set_up_logger(__name__)


"""
====================================================================
Objects Page: Address Group
====================================================================
"""


# Handles creation of a new address group from modal form submission.
@login_required(login_url="login")
def post_address_group_view(request):
    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None
    address_ids = [int(address_id) for address_id in request.POST.getlist("address_ids") if address_id]

    try:
        created_address_group = create_address_group(
            actor=request.user,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )

        if address_ids:
            add_addresses_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=created_address_group.id,
                address_ids=address_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/modals/_modal_form.html",
            {
                "modal_object_type": "addresses",
                "modal_content_partial": "partials/modals/_address_group_form.html",
                "modal_supports_types": True,
                "modal_type": "group",
                "item_type_editable": True,
                "modal_type_labels": {
                    "item": "Address",
                    "group": "Address Group",
                },
                "error_message": f"Could not create address group: {e}",
                "item_options": get_item_options_view(request, "addresses"),
            },
            status=400,
        )

    row = {
        "id": f"addressgroup-{created_address_group.id}",
        "cells": [
            "AddressGroup",
            created_address_group.name,
            created_address_group.description,
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


@login_required(login_url="login")
def update_address_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    name = request.POST.get("name", "")
    description = request.POST.get("description", "")
    address_ids = [int(address_id) for address_id in request.POST.getlist("address_ids") if address_id]

    object_data = {
        "name": name,
        "description": description,
        "addresses": [{"id": address_id} for address_id in address_ids],
    }

    if not tenant_id:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Address Group",
                "modal_mode": "update",
                "modal_row_id": f"addressgroup-{object_id}",
                "modal_object_type": "addresses",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_address_group_form.html",
                "modal_post_url": reverse("update-address-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-addresses"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "addresses"),
                "selected_address_ids": address_ids,
                "error_message": "No tenant selected.",
            },
            status=400,
        )

    try:
        update_address_group(
            actor=request.user,
            tenant_id=tenant_id,
            address_group_id=object_id,
            name=name,
            description=description,
        )

        AddressGroupMember.objects.filter(group_id=object_id).delete()

        if address_ids:
            add_addresses_to_group(
                actor=request.user,
                tenant_id=tenant_id,
                address_group_id=object_id,
                address_ids=address_ids,
            )

    except Exception as e:
        return render(
            request,
            "partials/_modal.html",
            {
                "modal_title": "Update Address Group",
                "modal_mode": "update",
                "modal_row_id": f"addressgroup-{object_id}",
                "modal_object_type": "addresses",
                "modal_type": "group",
                "modal_supports_types": False,
                "item_type_editable": False,
                "modal_type_labels": {},
                "modal_content_partial": "partials/modals/_address_group_form.html",
                "modal_post_url": reverse("update-address-group-view", args=[object_id]),
                "modal_target": "#modal-container",
                "modal_swap": "innerHTML",
                "modal_submit_handler": None,
                "modal_refresh_url": reverse("objects-addresses"),
                "object_data": object_data,
                "item_options": get_item_options_view(request, "addresses"),
                "selected_address_ids": address_ids,
                "error_message": f"Could not update address group: {e}",
            },
            status=400,
        )

    return HttpResponse(status=204)


# Handles deletion of an address group from the backend.
@login_required(login_url="login")
def delete_address_group_view(request, object_id):
    tenant_id = int(request.session.get("current_tenant_id")) if request.session.get("current_tenant_id") else None

    if not tenant_id:
        return HttpResponse("No tenant selected.", status=400)

    try:
        delete_address_group(
            actor=request.user,
            tenant_id=tenant_id,
            address_group_id=object_id,
        )
    except Exception as e:
        return HttpResponse(f"Could not delete address group: {e}", status=400)

    return HttpResponse(status=204)
