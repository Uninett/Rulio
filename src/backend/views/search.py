from django.urls import reverse

from backend.services.attribute_objects.get_address_objects import (
    get_all_address_groups_from_tenant,
    get_all_addresses_from_tenant,
)
from backend.services.attribute_objects.get_service_objects import (
    get_all_service_groups_from_tenant,
    get_all_services_from_tenant,
)
from backend.services.get import (
    get_all_device_groups_from_tenant,
    get_all_devices_from_tenant,
    get_all_filters_from_tenant,
    get_all_interfaces_from_tenant,
    get_all_rules_from_tenant,
    get_all_tags_from_tenant,
)
from backend.utils.logger import set_up_logger

# Setup logger
logger = set_up_logger(__name__)

"""
The server returns every searchable object for the tenant. Filtering and ranking
happens client side in partials/search/_search.html.
"""


TAG_PREFETCH = "tag_objects__tag"


def _tag_names(obj):
    return [tag_object.tag.name for tag_object in obj.tag_objects.all()]


def _searchable(*values):
    return " ".join(str(value) for value in values if value not in (None, "")).lower()


def _result(obj_id, name, obj_type, search_text, url, **extra):
    return {
        "id": obj_id,
        "name": name,
        "type": obj_type,
        "search_text": search_text,
        "url": url,
        **extra,
    }


def _get_tenant_id(request):
    tenant_id = request.session.get("current_tenant_id")
    return int(tenant_id) if tenant_id else None


def get_address_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    try:
        addresses = get_all_addresses_from_tenant(actor=request.user, tenant_id=tenant_id).prefetch_related(
            TAG_PREFETCH
        )
        address_groups = get_all_address_groups_from_tenant(actor=request.user, tenant_id=tenant_id).prefetch_related(
            TAG_PREFETCH
        )
    except Exception:
        logger.exception("Failed to fetch addresses for search")
        return {"results": []}

    url = f"{reverse('objects')}?object_type=addresses"
    matches = []

    for address in addresses:
        search_text = _searchable(
            address.id,
            address.name,
            address.description,
            address.addr_type,
            address.ipv4_type,
            address.ipv6_type,
            address.ipv4Network,
            address.ipv6Network,
            address.ipv4Address_start,
            address.ipv4Address_end,
            address.ipv6Address_start,
            address.ipv6Address_end,
            *_tag_names(address),
        )
        matches.append(
            _result(address.id, address.name, "Address", search_text, f"{url}&expand_id=address-{address.id}")
        )

    for group in address_groups:
        search_text = _searchable(group.id, group.name, group.description, *_tag_names(group))
        matches.append(
            _result(group.id, group.name, "AddressGroup", search_text, f"{url}&expand_id=addressgroup-{group.id}")
        )

    return {"results": matches}


def get_service_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    try:
        services = get_all_services_from_tenant(actor=request.user, tenant_id=tenant_id).prefetch_related(TAG_PREFETCH)
        service_groups = get_all_service_groups_from_tenant(actor=request.user, tenant_id=tenant_id).prefetch_related(
            TAG_PREFETCH
        )
    except Exception:
        logger.exception("Failed to fetch services for search")
        return {"results": []}

    url = f"{reverse('objects')}?object_type=services"
    matches = []

    for service in services:
        search_text = _searchable(
            service.id,
            service.name,
            service.description,
            service.protocol,
            service.port_start,
            service.port_end,
            service.icmp_type,
            service.icmp_code,
            *_tag_names(service),
        )
        matches.append(
            _result(service.id, service.name, "Service", search_text, f"{url}&expand_id=service-{service.id}")
        )

    for group in service_groups:
        search_text = _searchable(group.id, group.name, group.description, *_tag_names(group))
        matches.append(
            _result(group.id, group.name, "ServiceGroup", search_text, f"{url}&expand_id=servicegroup-{group.id}")
        )

    return {"results": matches}


def get_filter_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    try:
        filters = get_all_filters_from_tenant(actor=request.user, tenant_id=tenant_id).prefetch_related(TAG_PREFETCH)
    except Exception:
        logger.exception("Failed to fetch filters for search")
        return {"results": []}

    matches = []

    for filter_obj in filters:
        search_text = _searchable(filter_obj.id, filter_obj.name, filter_obj.description, *_tag_names(filter_obj))
        url = f"{reverse('filters')}?expand_id=filter-{filter_obj.id}"
        matches.append(_result(filter_obj.id, filter_obj.name, "Filter", search_text, url))

    return {"results": matches}


def get_rule_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    try:
        rules = (
            get_all_rules_from_tenant(actor=request.user, tenant_id=tenant_id)
            .select_related("filter")
            .prefetch_related(TAG_PREFETCH)
        )
    except Exception:
        logger.exception("Failed to fetch rules for search")
        return {"results": []}

    matches = []

    for rule in rules:
        search_text = _searchable(
            rule.id, rule.name, rule.description, rule.action, rule.filter.name, *_tag_names(rule)
        )
        url = f"{reverse('rules-page', args=[rule.filter_id])}?expand_id=rule-{rule.id}"
        matches.append(_result(rule.id, rule.name, "Rule", search_text, url))

    return {"results": matches}


def get_device_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    # The devices page only lists the tenant's own devices, so global ones would not be expandable
    try:
        devices = get_all_devices_from_tenant(
            actor=request.user, tenant_id=tenant_id, include_global_tenant=False
        ).prefetch_related(TAG_PREFETCH)
        device_groups = get_all_device_groups_from_tenant(
            actor=request.user, tenant_id=tenant_id, include_global_tenant=False
        ).prefetch_related(TAG_PREFETCH)
    except Exception:
        logger.exception("Failed to fetch devices for search")
        return {"results": []}

    url = reverse("devices")
    matches = []

    for device in devices:
        search_text = _searchable(
            device.id, device.name, device.platform, device.type, device.description, *_tag_names(device)
        )
        matches.append(_result(device.id, device.name, "Device", search_text, f"{url}?expand_id=device-{device.id}"))

    for group in device_groups:
        search_text = _searchable(group.id, group.name, group.description, *_tag_names(group))
        matches.append(
            _result(group.id, group.name, "DeviceGroup", search_text, f"{url}?expand_id=devicegroup-{group.id}")
        )

    return {"results": matches}


def get_interface_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    try:
        interfaces = get_all_interfaces_from_tenant(
            actor=request.user, tenant_id=tenant_id, include_global_tenant=False
        ).prefetch_related(TAG_PREFETCH)
    except Exception:
        logger.exception("Failed to fetch interfaces for search")
        return {"results": []}

    matches = []

    for interface in interfaces:
        search_text = _searchable(
            interface.id,
            interface.name,
            interface.type,
            interface.VRF,
            interface.description,
            interface.device.name,
            *_tag_names(interface),
        )
        url = reverse("interface-view", args=[interface.id])
        matches.append(_result(interface.id, interface.name, f"Interface ({interface.device.name})", search_text, url))

    return {"results": matches}


def get_tags_search_results(request):
    tenant_id = _get_tenant_id(request)
    if tenant_id is None:
        return {"results": []}

    try:
        tags = get_all_tags_from_tenant(actor=request.user, tenant_id=tenant_id)
    except Exception:
        logger.exception("Failed to fetch tags for search")
        return {"results": []}

    matches = []

    for tag in tags:
        search_text = _searchable(tag.id, tag.name, tag.tenant_id)
        url = f"{reverse('tags')}?object_type=tags&expand_id=tag-{tag.id}"
        matches.append(_result(tag.id, tag.name, "Tag", search_text, url, color=tag.color))

    return {"results": matches}


def get_global_search_results(request):
    results = []

    results.extend(get_address_search_results(request)["results"])
    results.extend(get_service_search_results(request)["results"])
    results.extend(get_filter_search_results(request)["results"])
    results.extend(get_rule_search_results(request)["results"])
    results.extend(get_device_search_results(request)["results"])
    results.extend(get_interface_search_results(request)["results"])
    results.extend(get_tags_search_results(request)["results"])

    return {"results": results}
