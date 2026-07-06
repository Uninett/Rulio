from backend.utils.logger import set_up_logger

from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)

from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)

logger = set_up_logger(__name__)

"""
====================================================================
Modal Partial
====================================================================
"""


# Fetch all groups of given object_type, by calling all items with "type"=AddressGroup/ServiceGroup
def get_group_options_view(request, object_type):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return []

    try:
        tenant_id = int(tenant_id)

        if object_type == "addresses":
            objects, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") == "AddressGroup"
            ]

        if object_type == "services":
            objects, _, _ = get_all_services_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") == "ServiceGroup"
            ]

    except Exception:
        return []

    return []


# Fetch all item options of given object_type, excluding groups.
def get_item_options_view(request, object_type):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return []

    try:
        tenant_id = int(tenant_id)

        if object_type == "addresses":
            objects, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") != "AddressGroup"
            ]

        if object_type == "services":
            objects, _, _ = get_all_services_and_groups_with_tags_from_tenant(
                actor=request.user,
                tenant_id=tenant_id,
            )

            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name", ""),
                }
                for item in objects
                if item.get("type") != "ServiceGroup"
            ]

    except Exception:
        return []

    return []
