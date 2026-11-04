import pytest
from django.urls import reverse

from backend.objects.filters.filter import Filter
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.attribute_objects.create_attribute_objects import create_tag
from backend.services.draft import store_changes
from backend.services.filter_draft import (
    FILTER_DRAFT_SCOPE,
    FILTER_DRAFT_SCOPE_ID,
    filter_changes_pending,
    get_filter_changes,
    saved_filter_key,
    stage_filter_create,
    stage_filter_delete,
    stage_filter_update,
)
from backend.services.filter_objects.create_filter_objects import (
    create_filter,
    create_rule,
)
from backend.services.membership import add_filter_to_interface
from backend.services.tenant_objects.create_tenant_objects import (
    create_device,
    create_interface,
)
from constants import GLOBAL_TENANT_ID


def filter_fields(name, **overrides):
    return {"name": name, "description": "", "tag_ids": [], **overrides}


@pytest.fixture
def filters_page(authenticated_user_and_tenant_id):
    user, tenant_id = authenticated_user_and_tenant_id
    filters = [
        create_filter(actor=user, tenant_id=tenant_id, name=name, description="")
        for name in ("Page filter B", "page filter D")
    ]
    return user, tenant_id, filters


def filters_html(client):
    return client.get(reverse("filters")).content.decode()


def row_ids_in_order(page_html, row_ids):
    return sorted(row_ids, key=lambda row_id: page_html.index(f'id="row-{row_id}"'))


def main_row(page_html, row_id):
    start = page_html.index(f'<tr id="row-{row_id}"')
    return page_html[start : page_html.index(">", start)]


def test_adding_a_filter_stages_it_without_saving(authenticated_client, filters_page):
    response = authenticated_client.post(reverse("post-filter-view"), {"name": "page-filter-new", "description": ""})

    page = filters_html(authenticated_client)
    assert response.status_code == 204
    assert not Filter.objects.filter(name="page-filter-new").exists()
    assert "page-filter-new" in page
    assert "row-diff-added" in page


def test_adding_a_filter_without_a_name_shows_an_error(authenticated_client, filters_page):
    response = authenticated_client.post(reverse("post-filter-view"), {"name": "", "description": ""})

    assert response.status_code == 400
    assert b"Missing required fields." in response.content


def test_editing_a_filter_stages_the_change(authenticated_client, filters_page):
    _user, _tenant_id, (filter_b, _filter_d) = filters_page
    update_url = reverse("update-filter-view", kwargs={"row_key": saved_filter_key(filter_b.id)})

    response = authenticated_client.post(update_url, {"name": "Page filter B", "description": "edited"})

    page = filters_html(authenticated_client)
    filter_b.refresh_from_db()
    assert response.status_code == 204
    assert filter_b.description == ""
    assert "row-diff-changed" in main_row(page, saved_filter_key(filter_b.id))
    assert 'title="Was: none"' in page


def test_deleting_a_filter_stages_the_deletion(authenticated_client, filters_page):
    _user, _tenant_id, (filter_b, _filter_d) = filters_page

    response = authenticated_client.post(
        reverse("delete-filter-view", kwargs={"row_key": saved_filter_key(filter_b.id)})
    )

    assert response.status_code == 204
    assert Filter.objects.filter(id=filter_b.id).exists()
    assert "row-diff-removed" in main_row(filters_html(authenticated_client), saved_filter_key(filter_b.id))


def test_rows_are_sorted_by_their_current_name(authenticated_client, filters_page):
    user, tenant_id, (filter_b, filter_d) = filters_page
    key_b, key_d = saved_filter_key(filter_b.id), saved_filter_key(filter_d.id)
    new_a = stage_filter_create(actor=user, tenant_id=tenant_id, fields=filter_fields("page filter A"))
    new_c = stage_filter_create(actor=user, tenant_id=tenant_id, fields=filter_fields("Page filter C"))
    stage_filter_update(actor=user, tenant_id=tenant_id, key=key_d, fields=filter_fields("page filter 0"))
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=key_b)

    page = filters_html(authenticated_client)

    assert row_ids_in_order(page, [new_a, new_c, key_b, key_d]) == [key_d, new_a, key_b, new_c]


def test_a_removed_filter_shows_what_saving_also_deletes(authenticated_client, filters_page):
    user, tenant_id, (filter_b, filter_d) = filters_page
    for name in ("page-rule-1", "page-rule-2", "page-rule-3"):
        create_rule(
            actor=user,
            filter=filter_b,
            tenant_id=tenant_id,
            name=name,
            description="",
            action="accept",
            enable=True,
            log_type="None",
            hit_count=0,
        )
    device = create_device(
        actor=user, tenant_id=tenant_id, name="page-device", description="", platform="juniper", type="firewall"
    )
    for direction in ("in", "out"):
        interface = create_interface(
            actor=user, tenant_id=tenant_id, name=f"page-if-{direction}", description="", type="", device_id=device.id
        )
        add_filter_to_interface(
            actor=user,
            tenant_id=tenant_id,
            filter_id=filter_b.id,
            interface_id=interface.id,
            policy_sequence=1,
            enable=True,
            direction=direction,
        )
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_b.id))
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_d.id))

    page = filters_html(authenticated_client)

    assert "Saving deletes its 3 rules and removes it from 2 interfaces." in page
    # A filter without rules or interfaces deletes nothing else.
    assert page.count("Unsaved deletion") == 1


def test_only_saved_filters_open_the_rules_page(authenticated_client, filters_page):
    user, tenant_id, (filter_b, filter_d) = filters_page
    new_key = stage_filter_create(actor=user, tenant_id=tenant_id, fields=filter_fields("page-filter-new"))
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_d.id))

    page = filters_html(authenticated_client)

    assert "navigateFromRow" in main_row(page, saved_filter_key(filter_b.id))
    assert "navigateFromRow" not in main_row(page, new_key)
    assert "navigateFromRow" not in main_row(page, saved_filter_key(filter_d.id))


def test_saving_writes_the_draft(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page
    stage_filter_create(actor=user, tenant_id=tenant_id, fields=filter_fields("page-filter-new"))
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_b.id))

    response = authenticated_client.post(reverse("save-filter-draft-view"))

    assert response.status_code == 204
    assert Filter.objects.filter(name="page-filter-new", tenant_id=tenant_id).exists()
    assert not Filter.objects.filter(id=filter_b.id).exists()
    assert "row-diff-" not in filters_html(authenticated_client)


def test_saving_reports_a_filter_deleted_by_someone_else(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page
    stage_filter_update(
        actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_b.id), fields=filter_fields("renamed")
    )
    Filter.objects.filter(id=filter_b.id).delete()

    response = authenticated_client.post(reverse("save-filter-draft-view"))

    assert response.status_code == 400
    assert b"was deleted by someone else" in response.content


def test_saving_reports_a_tenant_tag_on_a_global_filter(authenticated_client, filters_page):
    user, global_tenant_id, (filter_b, _filter_d) = filters_page
    other_tenant = Tenant.objects.create(tenant_name="Filters page tag tenant")
    assert authenticated_client.get(f"/api/set_tenant?tenant_id={other_tenant.id}").status_code == 200
    tag = create_tag(actor=user, tenant_id=other_tenant.id, name="page-tenant-tag", description="")
    # Written directly, as staging refuses it. filter_b belongs to the global tenant.
    changes = get_filter_changes(user, other_tenant.id)
    changes["updated"][saved_filter_key(filter_b.id)] = filter_fields("Page filter B", tag_ids=[tag.id])
    store_changes(user, other_tenant.id, FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID, changes)

    response = authenticated_client.post(reverse("save-filter-draft-view"))

    assert global_tenant_id == GLOBAL_TENANT_ID
    assert response.status_code == 400
    assert b"Could not save filter changes" in response.content
    assert not filter_b.get_tags().exists()
    assert filter_changes_pending(get_filter_changes(user, other_tenant.id))


def test_filter_draft_urls_only_accept_post(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page
    key_b = saved_filter_key(filter_b.id)
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=key_b)
    urls = [
        reverse("post-filter-view") + "?name=page-filter-new",
        reverse("update-filter-view", kwargs={"row_key": key_b}) + "?name=renamed",
        reverse("delete-filter-view", kwargs={"row_key": key_b}),
        reverse("save-filter-draft-view"),
        reverse("discard-filter-draft-view"),
    ]

    for url in urls:
        response = authenticated_client.get(url)
        assert response.status_code == 405, url

    assert Filter.objects.filter(id=filter_b.id).exists()
    assert not Filter.objects.filter(name="page-filter-new").exists()
    assert "row-diff-removed" in main_row(filters_html(authenticated_client), key_b)


def test_discarding_removes_the_draft(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_b.id))

    response = authenticated_client.post(reverse("discard-filter-draft-view"))

    assert response.status_code == 204
    assert "row-diff-removed" not in filters_html(authenticated_client)


def save_button(page_html):
    start = page_html.index('class="btn btn-save draft-save-btn"')
    return page_html[start : page_html.index("</button>", start)]


def test_filters_page_save_button_follows_the_draft(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page

    page = filters_html(authenticated_client)
    button = save_button(page)
    assert "filters-table draft-table" in page
    assert f'data-content-url="{reverse("filters-content")}"' in page
    assert 'data-draft-table="filters-table"' in button
    assert f'data-save-url="{reverse("save-filter-draft-view")}"' in button
    assert "disabled" in button

    stage_filter_delete(actor=user, tenant_id=tenant_id, key=saved_filter_key(filter_b.id))

    assert "disabled" not in save_button(filters_html(authenticated_client))


def test_edit_modal_shows_draft_values(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page
    key_b = saved_filter_key(filter_b.id)
    tag = create_tag(actor=user, tenant_id=tenant_id, name="page-filter-tag", description="")
    stage_filter_update(
        actor=user, tenant_id=tenant_id, key=key_b, fields=filter_fields("page-filter-renamed", tag_ids=[tag.id])
    )

    response = authenticated_client.get(reverse("modal-update", args=[key_b]))

    assert response.status_code == 200
    assert b'value="page-filter-renamed"' in response.content
    assert f'name="tag_ids" value="{tag.id}"'.encode() in response.content
    assert reverse("update-filter-view", kwargs={"row_key": key_b}).encode() in response.content


def test_edit_modal_opens_for_a_draft_only_filter(authenticated_client, filters_page):
    user, tenant_id, _filters = filters_page
    new_key = stage_filter_create(actor=user, tenant_id=tenant_id, fields=filter_fields("page-filter-new"))

    response = authenticated_client.get(reverse("modal-update", args=[new_key]))

    assert response.status_code == 200
    assert b'value="page-filter-new"' in response.content
    assert reverse("update-filter-view", kwargs={"row_key": new_key}).encode() in response.content
    assert reverse("delete-filter-view", kwargs={"row_key": new_key}).encode() in response.content


def test_edit_modal_refuses_a_filter_deleted_in_the_draft(authenticated_client, filters_page):
    user, tenant_id, (filter_b, _filter_d) = filters_page
    key_b = saved_filter_key(filter_b.id)
    stage_filter_delete(actor=user, tenant_id=tenant_id, key=key_b)

    response = authenticated_client.get(reverse("modal-update", args=[key_b]))

    assert response.status_code == 409
