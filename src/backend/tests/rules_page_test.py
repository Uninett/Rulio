import pytest
from django.urls import reverse

from backend.objects.filters.rule import Rule
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.rule_draft import (
    saved_rule_key,
    stage_rule_create,
    stage_rule_delete,
    stage_rule_enable_toggle,
    stage_rule_order,
    stage_rule_update,
)


def rule_fields(name):
    return {
        "name": name,
        "description": "",
        "action": "accept",
        "log_type": "None",
        "enable": True,
        "source_address_ids": [],
        "destination_address_ids": [],
        "source_service_ids": [],
        "destination_service_ids": [],
        "tag_ids": [],
    }


@pytest.fixture
def rules_page_filter(authenticated_user_and_tenant_id):
    user, tenant_id = authenticated_user_and_tenant_id
    filter_obj = create_filter(actor=user, tenant_id=tenant_id, name="Rules page filter", description="")
    rules = [
        create_rule(
            actor=user,
            filter=filter_obj,
            tenant_id=tenant_id,
            name=name,
            description="",
            action="accept",
            enable=True,
            log_type="None",
            hit_count=0,
        )
        for name in ("page-rule-a", "page-rule-b")
    ]
    return user, tenant_id, filter_obj, rules


@pytest.fixture
def rules_page_url(rules_page_filter):
    _user, _tenant_id, filter_obj, _rules = rules_page_filter
    return reverse("rules-page", kwargs={"filter_id": filter_obj.id})


def test_rules_page_shows_seq_and_enabled_columns(authenticated_client, rules_page_url):
    response = authenticated_client.get(rules_page_url)

    assert response.status_code == 200
    assert b">Seq</th>" in response.content
    assert b">Enabled</th>" in response.content


def test_rules_page_colours_draft_changes(authenticated_client, rules_page_filter, rules_page_url):
    user, tenant_id, filter_obj, (rule_a, rule_b) = rules_page_filter
    draft_args = {"actor": user, "tenant_id": tenant_id, "filter_id": filter_obj.id}
    stage_rule_create(**draft_args, fields=rule_fields("page-rule-new"))
    stage_rule_delete(**draft_args, key=saved_rule_key(rule_b.id))
    stage_rule_enable_toggle(**draft_args, key=saved_rule_key(rule_a.id))

    response = authenticated_client.get(rules_page_url)

    assert response.status_code == 200
    assert b"row-diff-added" in response.content
    assert b"row-diff-removed" in response.content
    assert b"row-diff-enabled-off" in response.content


def test_rules_page_shows_previous_sequence_for_dragged_rule(authenticated_client, rules_page_filter, rules_page_url):
    user, tenant_id, filter_obj, (rule_a, rule_b) = rules_page_filter
    key_a, key_b = saved_rule_key(rule_a.id), saved_rule_key(rule_b.id)
    stage_rule_order(actor=user, tenant_id=tenant_id, filter_id=filter_obj.id, order=[key_b, key_a], moved_key=key_b)

    response = authenticated_client.get(rules_page_url)

    assert response.status_code == 200
    assert '<span class="rule-seq-previous">2 → </span>' in response.content.decode()


def post_rule(client, filter_obj, name):
    return client.post(
        reverse("post-rule-view"),
        {"filter_id": filter_obj.id, "name": name, "description": "", "action": "accept", "log_type": "None"},
    )


def test_adding_a_rule_stages_it_without_saving(authenticated_client, rules_page_filter, rules_page_url):
    _user, _tenant_id, filter_obj, _rules = rules_page_filter

    response = post_rule(authenticated_client, filter_obj, "page-rule-new")

    assert response.status_code == 204
    assert not Rule.objects.filter(name="page-rule-new").exists()
    assert b"row-diff-added" in authenticated_client.get(rules_page_url).content


def test_adding_a_rule_with_a_taken_name_shows_an_error(authenticated_client, rules_page_filter):
    _user, _tenant_id, filter_obj, _rules = rules_page_filter

    response = post_rule(authenticated_client, filter_obj, "page-rule-a")

    assert response.status_code == 400
    assert b"A rule with this name already exists in this filter." in response.content


def test_editing_a_rule_stages_the_change(authenticated_client, rules_page_filter, rules_page_url):
    _user, _tenant_id, filter_obj, (rule_a, _rule_b) = rules_page_filter
    update_url = reverse("update-rule-view", kwargs={"filter_id": filter_obj.id, "row_key": saved_rule_key(rule_a.id)})

    response = authenticated_client.post(
        update_url, {"name": "page-rule-a", "description": "", "action": "deny", "log_type": "None", "enable": "on"}
    )

    assert response.status_code == 204
    rule_a.refresh_from_db()
    assert rule_a.action == "accept"
    assert b"row-diff-changed" in authenticated_client.get(rules_page_url).content


def test_edit_modal_shows_draft_values(authenticated_client, rules_page_filter):
    user, tenant_id, filter_obj, (rule_a, _rule_b) = rules_page_filter
    key_a = saved_rule_key(rule_a.id)
    stage_rule_update(actor=user, tenant_id=tenant_id, filter_id=filter_obj.id, key=key_a, fields=rule_fields("page-rule-renamed"))

    response = authenticated_client.get(reverse("modal-update", args=[key_a]) + f"?filter_id={filter_obj.id}")

    assert response.status_code == 200
    assert b'value="page-rule-renamed"' in response.content


def test_edit_modal_opens_for_a_draft_only_rule(authenticated_client, rules_page_filter):
    user, tenant_id, filter_obj, _rules = rules_page_filter
    new_key = stage_rule_create(actor=user, tenant_id=tenant_id, filter_id=filter_obj.id, fields=rule_fields("page-rule-new"))

    response = authenticated_client.get(reverse("modal-update", args=[new_key]) + f"?filter_id={filter_obj.id}")

    assert response.status_code == 200
    assert b'value="page-rule-new"' in response.content
    assert reverse("update-rule-view", kwargs={"filter_id": filter_obj.id, "row_key": new_key}).encode() in response.content


def test_deleting_a_rule_stages_the_deletion(authenticated_client, rules_page_filter, rules_page_url):
    _user, _tenant_id, filter_obj, (_rule_a, rule_b) = rules_page_filter
    delete_url = reverse("delete-rule-view", kwargs={"filter_id": filter_obj.id, "row_key": saved_rule_key(rule_b.id)})

    response = authenticated_client.post(delete_url)

    assert response.status_code == 204
    assert Rule.objects.filter(id=rule_b.id).exists()
    assert b"row-diff-removed" in authenticated_client.get(rules_page_url).content


def test_deleting_a_draft_only_rule_drops_it(authenticated_client, rules_page_filter, rules_page_url):
    user, tenant_id, filter_obj, _rules = rules_page_filter
    new_key = stage_rule_create(actor=user, tenant_id=tenant_id, filter_id=filter_obj.id, fields=rule_fields("page-rule-new"))

    response = authenticated_client.post(reverse("delete-rule-view", kwargs={"filter_id": filter_obj.id, "row_key": new_key}))

    page = authenticated_client.get(rules_page_url).content
    assert response.status_code == 204
    assert b"page-rule-new" not in page
    assert b"row-diff-added" not in page


def test_reordering_stages_the_order(authenticated_client, rules_page_filter, rules_page_url):
    _user, _tenant_id, filter_obj, (rule_a, rule_b) = rules_page_filter
    key_a, key_b = saved_rule_key(rule_a.id), saved_rule_key(rule_b.id)

    response = authenticated_client.post(
        reverse("reorder-rule-view", kwargs={"filter_id": filter_obj.id}),
        {"order": f"{key_b},{key_a}", "moved_key": key_b},
    )

    assert response.status_code == 204
    rule_a.refresh_from_db()
    rule_b.refresh_from_db()
    assert (rule_a.rule_sequence, rule_b.rule_sequence) == (1, 2)
    assert '<span class="rule-seq-previous">2 → </span>' in authenticated_client.get(rules_page_url).content.decode()


def test_reordering_with_an_incomplete_order_is_refused(authenticated_client, rules_page_filter):
    _user, _tenant_id, filter_obj, (rule_a, _rule_b) = rules_page_filter
    key_a = saved_rule_key(rule_a.id)

    response = authenticated_client.post(
        reverse("reorder-rule-view", kwargs={"filter_id": filter_obj.id}),
        {"order": key_a, "moved_key": key_a},
    )

    assert response.status_code == 400
    assert b"The rule list has changed" in response.content


def test_toggling_enable_stages_the_change(authenticated_client, rules_page_filter, rules_page_url):
    _user, _tenant_id, filter_obj, (rule_a, _rule_b) = rules_page_filter
    toggle_url = reverse(
        "toggle-rule-enable-view", kwargs={"filter_id": filter_obj.id, "row_key": saved_rule_key(rule_a.id)}
    )

    response = authenticated_client.post(toggle_url)

    assert response.status_code == 204
    rule_a.refresh_from_db()
    assert rule_a.enable is True
    assert b"row-diff-enabled-off" in authenticated_client.get(rules_page_url).content


def test_saving_writes_the_draft(authenticated_client, rules_page_filter, rules_page_url):
    user, tenant_id, filter_obj, (_rule_a, rule_b) = rules_page_filter
    draft_args = {"actor": user, "tenant_id": tenant_id, "filter_id": filter_obj.id}
    stage_rule_create(**draft_args, fields=rule_fields("page-rule-new"))
    stage_rule_delete(**draft_args, key=saved_rule_key(rule_b.id))

    response = authenticated_client.post(reverse("save-rule-draft-view", kwargs={"filter_id": filter_obj.id}))

    page = authenticated_client.get(rules_page_url).content
    assert response.status_code == 204
    assert Rule.objects.filter(name="page-rule-new", filter=filter_obj).exists()
    assert not Rule.objects.filter(id=rule_b.id).exists()
    assert b"row-diff-" not in page


def test_saving_reports_a_rule_deleted_by_someone_else(authenticated_client, rules_page_filter):
    user, tenant_id, filter_obj, (rule_a, _rule_b) = rules_page_filter
    stage_rule_update(
        actor=user,
        tenant_id=tenant_id,
        filter_id=filter_obj.id,
        key=saved_rule_key(rule_a.id),
        fields={**rule_fields("page-rule-a"), "action": "deny"},
    )
    Rule.objects.filter(id=rule_a.id).delete()

    response = authenticated_client.post(reverse("save-rule-draft-view", kwargs={"filter_id": filter_obj.id}))

    assert response.status_code == 400
    assert b"was deleted by someone else" in response.content


def test_discarding_removes_the_draft(authenticated_client, rules_page_filter, rules_page_url):
    user, tenant_id, filter_obj, (_rule_a, rule_b) = rules_page_filter
    stage_rule_delete(actor=user, tenant_id=tenant_id, filter_id=filter_obj.id, key=saved_rule_key(rule_b.id))

    response = authenticated_client.post(reverse("discard-rule-draft-view", kwargs={"filter_id": filter_obj.id}))

    assert response.status_code == 204
    assert b"row-diff-removed" not in authenticated_client.get(rules_page_url).content


def save_button(page_html):
    start = page_html.index('class="btn btn-save draft-save-btn"')
    return page_html[start : page_html.index("</button>", start)]


def test_rules_page_save_buttons_follow_the_draft(authenticated_client, rules_page_filter, rules_page_url):
    user, tenant_id, filter_obj, (rule_a, _rule_b) = rules_page_filter
    save_url = reverse("save-rule-draft-view", kwargs={"filter_id": filter_obj.id})

    button = save_button(authenticated_client.get(rules_page_url).content.decode())
    assert "saveRuleChanges(this)" in button
    assert f'data-save-url="{save_url}"' in button
    assert "disabled" in button

    stage_rule_enable_toggle(actor=user, tenant_id=tenant_id, filter_id=filter_obj.id, key=saved_rule_key(rule_a.id))

    button = save_button(authenticated_client.get(rules_page_url).content.decode())
    assert "disabled" not in button
