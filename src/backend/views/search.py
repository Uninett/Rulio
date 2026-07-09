from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.urls import reverse


from backend.services.attribute_objects.get_address_objects import (
    get_all_addresses_and_groups_with_tags_from_tenant,
)
from backend.services.attribute_objects.get_service_objects import (
    get_all_services_and_groups_with_tags_from_tenant,
)

from backend.services.get import (
    get_all_tags_from_tenant,
)


def get_address_search_results(request, query):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {{"results": []}}

    try:
        result, _, _ = get_all_addresses_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
            include_global_tenant=False,
        )
    except Exception:
        return {{"results": []}}

    query = query.lower()

    matches = []

    for item in result:
        searchable_text = " ".join(str(value).lower() for value in item.values()).lower()
        print(f"Searching for '{query}' in '{searchable_text}'")
        row_id = f"{item.get('type', '').lower()}-{item.get('id')}"

        if query in searchable_text:
            matches.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "type": item["type"],
                    "display": f"{item['name'], item['type']}",
                    "search_text": searchable_text,
                    "url": f"{reverse('objects')}?object_type=addresses&expand_id={row_id}",
                }
            )

    return {"results": matches}


def get_service_search_results(request, query):
    tenant_id = request.session.get("current_tenant_id")
    if not tenant_id:
        return {{"results": []}}

    try:
        services, _, _ = get_all_services_and_groups_with_tags_from_tenant(
            actor=request.user,
            tenant_id=int(tenant_id),
            include_global_tenant=False,
        )
    except Exception:
        return {{"results": []}}

    query = query.lower()
    matches = []

    for item in services:
        searchable_text = " ".join(str(value).lower() for value in item.values()).lower()
        print(f"Searching for '{query}' in '{searchable_text}'")
        row_id = f"{item.get('type', '').lower()}-{item.get('id')}"

        if query in searchable_text:
            matches.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "type": item["type"],
                    "display": f"{item['name'], item['type']}",
                    "search_text": searchable_text,
                    "url": f"{reverse('objects')}?object_type=services&expand_id={row_id}",
                }
            )

    return {"results": matches}


def get_tags_search_results(request, query):
    tenant_id = request.session.get("current_tenant_id")
    tags = get_all_tags_from_tenant(
        actor=request.user,
        tenant_id=int(tenant_id),
    )
    query = query.lower()
    matches = []

    for item in tags:
        searchable_text = f"{item.id} {item.name} {item.tenant_id}".lower()
        print(f"Searching for '{query}' in '{searchable_text}'")

        row_id = f"tag-{item.id}"

        if query in searchable_text:
            matches.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "type": "Tag",
                    "display": item.name,
                    "search_text": searchable_text,
                    "url": f"{reverse('tags')}?object_type=tags&expand_id={row_id}",
                }
            )

    return {"results": matches}


def get_global_search_results(request):

    results = []

    results.extend(get_address_search_results(request, "")["results"])
    results.extend(get_service_search_results(request, "")["results"])
    results.extend(get_tags_search_results(request, "")["results"])

    return {"results": results}
