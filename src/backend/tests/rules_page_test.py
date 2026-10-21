import pytest
from django.urls import reverse

from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.rule_draft import (
    saved_rule_key,
    stage_rule_create,
    stage_rule_delete,
    stage_rule_enable_toggle,
    stage_rule_order,
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
