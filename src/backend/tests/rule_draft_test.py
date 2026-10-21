import pytest

from backend.objects.draft import Draft
from backend.objects.filters.rule import Rule
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.rule_draft import (
    RuleDraftError,
    apply_rule_draft,
    build_rule_changeset,
    discard_rule_draft,
    get_rule_changes,
    load_baseline_rules,
    saved_rule_key,
    stage_rule_create,
    stage_rule_delete,
    stage_rule_enable_toggle,
    stage_rule_order,
    stage_rule_update,
)


def rule_fields(name, **overrides):
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
        **overrides,
    }


@pytest.fixture
def rules_filter(superuser, create_testing_tenant):
    filter_obj = create_filter(
        actor=superuser,
        tenant_id=create_testing_tenant.id,
        name="Draft test filter",
        description="",
    )
    rules = [
        create_rule(
            actor=superuser,
            filter=filter_obj,
            tenant_id=create_testing_tenant.id,
            name=name,
            description="",
            action="accept",
            enable=True,
            log_type="None",
            hit_count=0,
        )
        for name in ("draft-rule-a", "draft-rule-b", "draft-rule-c")
    ]
    return filter_obj, rules


@pytest.fixture
def draft_args(superuser, create_testing_tenant, rules_filter):
    filter_obj, _rules = rules_filter
    return {"actor": superuser, "tenant_id": create_testing_tenant.id, "filter_id": filter_obj.id}


def changeset_for(draft_args):
    baseline = load_baseline_rules(draft_args["actor"], draft_args["tenant_id"], draft_args["filter_id"])
    return build_rule_changeset(baseline, get_rule_changes(draft_args["actor"], draft_args["filter_id"]))


def entry_for(changeset, key):
    return next(entry for entry in changeset if entry["key"] == key)


def test_staged_create_is_not_saved_until_draft_is_applied(draft_args):
    stage_rule_create(**draft_args, fields=rule_fields("draft-rule-new"))

    assert not Rule.objects.filter(name="draft-rule-new").exists()

    apply_rule_draft(**draft_args)

    assert Rule.objects.filter(name="draft-rule-new", filter_id=draft_args["filter_id"]).exists()
    assert not Draft.objects.filter(user=draft_args["actor"]).exists()


def test_changeset_marks_added_removed_and_changed_rules(draft_args, rules_filter):
    _filter_obj, (rule_a, rule_b, rule_c) = rules_filter
    new_key = stage_rule_create(**draft_args, fields=rule_fields("draft-rule-new"))
    stage_rule_delete(**draft_args, key=saved_rule_key(rule_b.id))
    stage_rule_update(**draft_args, key=saved_rule_key(rule_c.id), fields=rule_fields("draft-rule-c", action="deny"))

    changeset = changeset_for(draft_args)

    assert [entry["key"] for entry in changeset] == [
        saved_rule_key(rule_a.id),
        saved_rule_key(rule_b.id),
        saved_rule_key(rule_c.id),
        new_key,
    ]
    assert entry_for(changeset, saved_rule_key(rule_a.id))["status"] == "unchanged"
    assert entry_for(changeset, saved_rule_key(rule_b.id))["status"] == "removed"
    assert entry_for(changeset, saved_rule_key(rule_b.id))["previous_sequence"] == 2
    assert entry_for(changeset, saved_rule_key(rule_c.id))["status"] == "changed"
    assert entry_for(changeset, saved_rule_key(rule_c.id))["changed_fields"] == ["action"]
    assert entry_for(changeset, new_key)["status"] == "added"


def test_enable_toggle_is_an_enable_change_not_a_field_change(draft_args, rules_filter):
    _filter_obj, (rule_a, _rule_b, _rule_c) = rules_filter
    stage_rule_enable_toggle(**draft_args, key=saved_rule_key(rule_a.id))

    entry = entry_for(changeset_for(draft_args), saved_rule_key(rule_a.id))

    assert entry["enable_changed"] is True
    assert entry["changed_fields"] == []
    assert entry["fields"]["enable"] is False


def test_only_the_dragged_rule_is_marked_as_moved(draft_args, rules_filter):
    _filter_obj, (rule_a, rule_b, rule_c) = rules_filter
    key_a, key_b, key_c = (saved_rule_key(rule.id) for rule in (rule_a, rule_b, rule_c))
    stage_rule_order(**draft_args, order=[key_c, key_a, key_b], moved_key=key_c)

    changeset = changeset_for(draft_args)

    assert entry_for(changeset, key_c)["moved"] is True
    assert entry_for(changeset, key_c)["previous_sequence"] == 3
    assert entry_for(changeset, key_c)["sequence"] == 1
    assert entry_for(changeset, key_a)["moved"] is False
    assert entry_for(changeset, key_a)["status"] == "unchanged"


def test_editing_a_rule_back_to_its_saved_values_clears_the_draft(draft_args, rules_filter):
    _filter_obj, (rule_a, _rule_b, _rule_c) = rules_filter
    key_a = saved_rule_key(rule_a.id)
    stage_rule_update(**draft_args, key=key_a, fields=rule_fields("draft-rule-a", action="deny"))
    stage_rule_update(**draft_args, key=key_a, fields=rule_fields("draft-rule-a"))

    assert not Draft.objects.filter(user=draft_args["actor"]).exists()


def test_deleting_a_rule_created_in_the_draft_drops_it(draft_args):
    new_key = stage_rule_create(**draft_args, fields=rule_fields("draft-rule-new"))
    stage_rule_delete(**draft_args, key=new_key)

    assert not Draft.objects.filter(user=draft_args["actor"]).exists()


def test_duplicate_rule_names_in_the_same_filter_are_rejected(draft_args):
    with pytest.raises(RuleDraftError):
        stage_rule_create(**draft_args, fields=rule_fields("draft-rule-a"))


def test_the_same_rule_name_is_allowed_in_another_filter(superuser, create_testing_tenant, rules_filter):
    other_filter = create_filter(
        actor=superuser,
        tenant_id=create_testing_tenant.id,
        name="Other draft test filter",
        description="",
    )

    create_rule(
        actor=superuser,
        filter=other_filter,
        tenant_id=create_testing_tenant.id,
        name="draft-rule-a",
        description="",
        action="accept",
        enable=True,
        log_type="None",
        hit_count=0,
    )
    stage_rule_create(
        actor=superuser,
        tenant_id=create_testing_tenant.id,
        filter_id=other_filter.id,
        fields=rule_fields("draft-rule-b"),
    )

    assert Rule.objects.filter(name="draft-rule-a").count() == 2


def test_apply_saves_updates_deletes_and_order(draft_args, rules_filter):
    _filter_obj, (rule_a, rule_b, rule_c) = rules_filter
    key_a, key_b, key_c = (saved_rule_key(rule.id) for rule in (rule_a, rule_b, rule_c))
    stage_rule_update(**draft_args, key=key_a, fields=rule_fields("draft-rule-a", action="deny"))
    stage_rule_delete(**draft_args, key=key_b)
    stage_rule_order(**draft_args, order=[key_c, key_a], moved_key=key_c)

    apply_rule_draft(**draft_args)

    remaining = list(Rule.objects.filter(filter_id=draft_args["filter_id"]).order_by("rule_sequence"))
    assert [rule.name for rule in remaining] == ["draft-rule-c", "draft-rule-a"]
    assert [rule.rule_sequence for rule in remaining] == [1, 2]
    assert remaining[1].action == "deny"
    assert not Draft.objects.filter(user=draft_args["actor"]).exists()


def test_apply_stops_when_a_rule_was_deleted_by_someone_else(draft_args, rules_filter):
    _filter_obj, (rule_a, rule_b, _rule_c) = rules_filter
    stage_rule_update(**draft_args, key=saved_rule_key(rule_a.id), fields=rule_fields("draft-rule-a", action="deny"))
    stage_rule_delete(**draft_args, key=saved_rule_key(rule_b.id))
    Rule.objects.filter(id=rule_a.id).delete()

    with pytest.raises(RuleDraftError):
        apply_rule_draft(**draft_args)

    assert Rule.objects.filter(id=rule_b.id).exists()
    assert Draft.objects.filter(user=draft_args["actor"]).exists()


def test_discard_removes_the_draft(draft_args):
    stage_rule_create(**draft_args, fields=rule_fields("draft-rule-new"))

    discard_rule_draft(draft_args["actor"], draft_args["filter_id"])

    assert not Draft.objects.filter(user=draft_args["actor"]).exists()
