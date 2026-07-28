from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.objects.filters.rule import Rule
from backend.services.attribute_objects.get_address_objects import get_address_group_members
from backend.services.attribute_objects.get_service_objects import get_service_group_members
from backend.views.modal import get_group_options_view, get_item_options_view
from backend.views.session import get_tenant_context
from django.urls import reverse

from backend.services.get import get_filters_with_rules_with_tags_from_tenant, get_all_rules_with_objects_from_filter

"""
====================================================================
Rule Page
====================================================================
"""


@login_required(login_url="login")
def get_rule_page(request):
    request.session["active_page"] = "Filter -> Rule -> " + request.GET.get("filter_name", "")
    return render(
        request,
        "rules.html",
        {
            "active_page": "rules",
            "page_title": "Filter -> " + request.GET.get("filter_name", ""),
            "object_type": "rules",
            "object_extra_type": "filter",
            "add_button_label": "Add Rule",
            "rules": get_rules_view(request),
            **get_tenant_context(request),
        },
    )


def get_rules_view(request):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {"headers": [], "rows": []}

    tenant_id = int(tenant_id)

    headers = [
        "Name",
        "Source",
        "Destination",
        "Services",
        "Action",
        "Log",
        "Count",
        "Description",
        "Created",
        "Modified",
        "Tags",
    ]

    filter_id = request.GET.get("filter_id")
    if not filter_id:
        return {"headers": headers, "rows": []}

    try:
        rules = get_all_rules_with_objects_from_filter(
            request.user,
            tenant_id,
            int(filter_id),
        )
    except Exception as e:
        print(f"Error fetching rules with objects for filter {filter_id}: {e}")
        return {"headers": headers, "rows": []}

    rows = []

    for rule in rules:
        try:
            rule_obj = Rule.objects.get(id=rule["rule_id"])
            rule_tag_names = [tag.name for tag in rule_obj.get_tags()]
        except Exception as e:
            print(f"Error fetching tags for rule {rule['rule_id']}: {e}")
            rule_tag_names = []

        source_objects = []
        destination_objects = []
        service_objects = []

        for obj in rule["objects"]:
            object_type = (obj.get("object_type") or "").lower()
            object_id = obj.get("object_id")
            object_name = obj.get("object_name") or ""
            row_id = f"{object_type}-{object_id}" if object_type and object_id else ""

            navigate_url = ""
            if object_type in ["address", "addressgroup"]:
                navigate_url = reverse("objects") + f"?object_type=addresses&expand_id={row_id}"
            elif object_type in ["service", "servicegroup"]:
                navigate_url = reverse("objects") + f"?object_type=services&expand_id={row_id}"

            item = {
                "name": object_name,
                "row_id": row_id,
                "navigate_url": navigate_url,
                "hover_text": object_name,
            }

            match object_type:
                case "address" | "addressgroup":
                    if obj["match_type"] == "source":
                        source_objects.append(item)
                    elif obj["match_type"] == "destination":
                        destination_objects.append(item)

                case "service" | "servicegroup":
                    service_objects.append(item)

        rows.append(
            {
                "id": f"rule-{rule['rule_id']}",
                "is_group": False,
                "cells": [
                    rule["rule_name"],
                    source_objects,
                    destination_objects,
                    service_objects,
                    rule["rule_action"],
                    rule["rule_log_type"],
                    str(rule["rule_hit_count"]),
                    rule["rule_description"] or "",
                    rule["rule_date_created"].strftime("%Y-%m-%d %H:%M") if rule["rule_date_created"] else "",
                    rule["rule_date_changed"].strftime("%Y-%m-%d %H:%M") if rule["rule_date_changed"] else "",
                    rule_tag_names,
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }


@login_required(login_url="login")
def post_rule_view(request):
    name = request.POST.get("name")
    description = request.POST.get("description")
    action = request.POST.get("action")
    log_type = request.POST.get("log_type")
    filter_id = request.POST.get("filter_id")

    if not all([name, action, log_type, filter_id]):
        return {"success": False, "message": "Missing required fields."}

    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {"success": False, "message": "Tenant not set."}

    tenant_id = int(tenant_id)

    try:
        new_rule = create_rule(
            actor=request.user,
            name=name,
            description=description,
            action=action,
            log_type=log_type,
            filter_id=int(filter_id),
            tenant_id=tenant_id,
        )
        return {"success": True, "message": "Rule created successfully.", "rule_id": new_rule.id}
    except Exception as e:
        print(f"Error creating rule: {e}")
        return {"success": False, "message": "Error creating rule."}


@login_required(login_url="login")
def get_rule_selector_modal(request, selector_type):
    context = {
        "modal_title": f"Edit {selector_type.title()}",
        "modal_mode": "submodal",
        "modal_object_type": "rule-selector",
        "modal_content_partial": "partials/modals/_rule_selector_modal.html",
        "selector_type": selector_type,
    }

    if selector_type in ["source", "destination"]:
        context["item_options"] = get_item_options_view(request, "addresses")
        context["selected_address_ids"] = []
        context["group_options"] = get_group_options_view(request, "addresses")
        context["selected_group_ids"] = []

    elif selector_type == "service":
        context["item_options"] = get_item_options_view(request, "services")
        context["selected_service_ids"] = []
        context["group_options"] = get_group_options_view(request, "services")
        context["selected_group_ids"] = []

    return render(request, "partials/_modal.html", context)
