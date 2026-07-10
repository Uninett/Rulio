from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from backend.objects.filters.rule import Rule
from backend.services.attribute_objects.get_address_objects import get_address_group_members
from backend.services.attribute_objects.get_service_objects import get_service_group_members
from backend.views.session import get_tenant_context

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
        return {
            "headers": [],
            "rows": [],
        }

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
        return {
            "headers": headers,
            "rows": [],
        }

    try:
        rules = get_all_rules_with_objects_from_filter(
            request.user,
            tenant_id,
            int(filter_id),
        )
    except Exception as e:
        print(f"Error fetching rules with objects for filter {filter_id}: {e}")
        return {
            "headers": headers,
            "rows": [],
        }

    rows = []

    for rule in rules:
        try:
            rule_obj = Rule.objects.get(id=rule["rule_id"])
            rule_tag_names = [tag.name for tag in rule_obj.get_tags()]
        except Exception as e:
            print(f"Error fetching tags for rule {rule['rule_id']}: {e}")
            rule_tag_names = []

        address_source = []
        address_destination = []
        services = []

        try:
            for obj in rule["objects"]:
                object_type = (obj.get("object_type") or "").lower()

                match object_type:
                    case "address":
                        if obj["match_type"] == "source":
                            address_source.append(obj["object_name"])
                        elif obj["match_type"] == "destination":
                            address_destination.append(obj["object_name"])

                    case "service":
                        services.append(obj["object_name"])

                    case "addressgroup":
                        if obj["match_type"] == "source":
                            addresses = get_address_group_members(
                                request.user,
                                tenant_id,
                                obj["object_id"],
                            )
                            address_source.extend([address.name for address in addresses])

                        elif obj["match_type"] == "destination":
                            addresses = get_address_group_members(
                                request.user,
                                tenant_id,
                                obj["object_id"],
                            )
                            address_destination.extend([address.name for address in addresses])

                    case "servicegroup":
                        servicegroup = get_service_group_members(
                            request.user,
                            tenant_id,
                            obj["object_id"],
                        )
                        services.extend([service.name for service in servicegroup])

        except Exception as e:
            print(f"Error fetching objects for rule {rule['rule_id']}: {e}")

        rows.append(
            {
                "id": f"rule-{rule['rule_id']}",
                "is_group": False,
                "cells": [
                    rule["rule_name"],
                    address_source,
                    address_destination,
                    services,
                    rule["rule_action"],
                    rule["rule_log_type"],
                    rule["rule_hit_count"],
                    rule["rule_description"] or "",
                    rule["rule_date_created"] or "",
                    rule["rule_date_changed"] or "",
                    rule_tag_names,
                ],
            }
        )

    return {
        "headers": headers,
        "rows": rows,
    }
