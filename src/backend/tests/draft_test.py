import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from backend.objects.draft import Draft
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.draft import (
    DraftError,
    build_changeset,
    changes_pending,
    discard_draft,
    effective_fields,
    empty_changes,
    get_changes,
    is_new_key,
    key_type,
    new_key,
    require_editable_row,
    require_rows_still_exist,
    saved_key,
    set_row_fields,
    stage_create,
    stage_delete,
    store_changes,
)

FIELD_NAMES = ("name", "description", "enable")


@pytest.fixture
def draft_owner(superuser, create_testing_tenant):
    return {"actor": superuser, "tenant_id": create_testing_tenant.id}


@pytest.fixture
def baseline(create_testing_tenant):
    return [
        {"key": "filter-1", "tenant_id": create_testing_tenant.id, "fields": filter_fields("a")},
        {"key": "filter-2", "tenant_id": create_testing_tenant.id, "fields": filter_fields("b")},
    ]


@pytest.fixture
def baseline_by_key(baseline):
    return {row["key"]: row for row in baseline}


# A user without write access to the test tenant.
@pytest.fixture
def reader(db):
    return get_user_model().objects.create_user(username="draft-reader", password="x")


def changes_with_created(name, object_type="filter"):
    changes = empty_changes()
    changes["created"][new_key(object_type, changes)] = {"name": name}
    return changes


def filter_fields(name, **overrides):
    return {"name": name, "description": "", "enable": True, **overrides}


def test_saved_key_is_the_row_id():
    assert saved_key("address", 1) == "address-1"


def test_new_keys_count_up_per_draft():
    changes = empty_changes()

    assert new_key("address", changes) == "addressdraft-1"
    assert new_key("addressgroup", changes) == "addressgroupdraft-2"


def test_key_type_and_is_new_key_read_both_kinds_of_key():
    assert key_type("addressgroup-4") == "addressgroup"
    assert key_type("addressgroupdraft-1") == "addressgroup"
    assert not is_new_key("addressgroup-4")
    assert is_new_key("addressgroupdraft-1")


def test_no_draft_gives_empty_changes(draft_owner):
    assert get_changes(**draft_owner, scope="filters", scope_id=0) == empty_changes()


def test_stored_changes_are_read_back(draft_owner):
    changes = changes_with_created("new filter")

    store_changes(**draft_owner, scope="filters", scope_id=0, changes=changes)

    assert get_changes(**draft_owner, scope="filters", scope_id=0) == changes


def test_storing_again_updates_the_same_draft(draft_owner):
    store_changes(**draft_owner, scope="filters", scope_id=0, changes=changes_with_created("first filter"))
    changes = changes_with_created("second filter")

    store_changes(**draft_owner, scope="filters", scope_id=0, changes=changes)

    assert Draft.objects.filter(user=draft_owner["actor"]).count() == 1
    assert get_changes(**draft_owner, scope="filters", scope_id=0) == changes


def test_storing_no_changes_removes_the_draft(draft_owner):
    store_changes(**draft_owner, scope="filters", scope_id=0, changes=changes_with_created("new filter"))

    store_changes(**draft_owner, scope="filters", scope_id=0, changes=empty_changes())

    assert not Draft.objects.filter(user=draft_owner["actor"]).exists()


def test_a_changed_order_counts_as_pending():
    assert not changes_pending(empty_changes())
    assert changes_pending({**empty_changes(), "order": ["rule-1"]})


def test_drafts_are_kept_apart_by_tenant_scope_and_scope_id(draft_owner):
    other_tenant = Tenant.objects.create(tenant_name="Second draft tenant")
    store_changes(**draft_owner, scope="filter_rules", scope_id=1, changes=changes_with_created("new rule", "rule"))

    assert get_changes(draft_owner["actor"], other_tenant.id, "filter_rules", 1) == empty_changes()
    assert get_changes(**draft_owner, scope="filters", scope_id=1) == empty_changes()
    assert get_changes(**draft_owner, scope="filter_rules", scope_id=2) == empty_changes()


def test_another_users_draft_is_not_visible(draft_owner):
    other_user = get_user_model().objects.create_user(username="second-draft-user", password="x")
    store_changes(**draft_owner, scope="filters", scope_id=0, changes=changes_with_created("new filter"))

    assert get_changes(other_user, draft_owner["tenant_id"], "filters", 0) == empty_changes()


def test_missing_keys_in_a_stored_draft_are_filled_in(draft_owner):
    created = {"filterdraft-1": {"name": "new filter"}}
    Draft.objects.create(
        user=draft_owner["actor"],
        tenant_id=draft_owner["tenant_id"],
        scope="filters",
        scope_id=0,
        changes={"created": created},
    )

    assert get_changes(**draft_owner, scope="filters", scope_id=0) == {**empty_changes(), "created": created}


def test_discard_only_removes_that_draft(draft_owner):
    rule_changes = changes_with_created("new rule", "rule")
    store_changes(**draft_owner, scope="filters", scope_id=0, changes=changes_with_created("new filter"))
    store_changes(**draft_owner, scope="filter_rules", scope_id=1, changes=rule_changes)

    discard_draft(**draft_owner, scope="filters", scope_id=0)

    assert get_changes(**draft_owner, scope="filters", scope_id=0) == empty_changes()
    assert get_changes(**draft_owner, scope="filter_rules", scope_id=1) == rule_changes


def test_effective_fields_prefers_created_then_updated_then_saved(baseline_by_key):
    changes = empty_changes()
    changes["created"]["filterdraft-1"] = filter_fields("new")
    changes["updated"]["filter-1"] = filter_fields("edited")

    assert effective_fields("filterdraft-1", baseline_by_key, changes)["name"] == "new"
    assert effective_fields("filter-1", baseline_by_key, changes)["name"] == "edited"
    assert effective_fields("filter-2", baseline_by_key, changes)["name"] == "b"


def test_set_row_fields_stores_an_edit_of_a_saved_row(baseline_by_key):
    changes = empty_changes()

    set_row_fields("filter-1", filter_fields("edited"), baseline_by_key, changes)

    assert changes["updated"] == {"filter-1": filter_fields("edited")}


def test_set_row_fields_drops_a_row_edited_back_to_saved(baseline_by_key):
    changes = empty_changes()
    set_row_fields("filter-1", filter_fields("edited"), baseline_by_key, changes)

    set_row_fields("filter-1", filter_fields("a"), baseline_by_key, changes)

    assert changes["updated"] == {}


def test_set_row_fields_replaces_a_created_row(baseline_by_key):
    changes = empty_changes()
    key = stage_create(changes, "filter", filter_fields("new"))

    set_row_fields(key, filter_fields("renamed"), baseline_by_key, changes)

    assert changes["created"] == {key: filter_fields("renamed")}
    assert changes["updated"] == {}


def test_stage_create_takes_the_next_key():
    changes = empty_changes()

    first = stage_create(changes, "filter", filter_fields("x"))
    second = stage_create(changes, "filter", filter_fields("y"))

    assert (first, second) == ("filterdraft-1", "filterdraft-2")
    assert list(changes["created"]) == [first, second]
    assert "order" not in changes


def test_stage_create_appends_to_a_changed_order():
    changes = {**empty_changes(), "order": ["filter-2", "filter-1"]}

    key = stage_create(changes, "filter", filter_fields("x"))

    assert changes["order"] == ["filter-2", "filter-1", key]


def test_stage_create_leaves_an_unchanged_order_alone():
    changes = {**empty_changes(), "order": None}

    stage_create(changes, "filter", filter_fields("x"))

    assert changes["order"] is None


def test_stage_delete_drops_a_created_row_completely():
    changes = {**empty_changes(), "order": ["filter-1"], "moved": []}
    key = stage_create(changes, "filter", filter_fields("x"))
    changes["moved"].append(key)

    stage_delete(changes, key)

    assert changes["created"] == {}
    assert changes["deleted"] == []
    assert changes["order"] == ["filter-1"]
    assert changes["moved"] == []


def test_stage_delete_marks_a_saved_row_deleted_and_drops_its_edit():
    changes = {**empty_changes(), "order": ["filter-2", "filter-1"], "moved": ["filter-1"]}
    changes["updated"]["filter-1"] = filter_fields("edited")

    stage_delete(changes, "filter-1")

    assert changes["updated"] == {}
    assert changes["deleted"] == ["filter-1"]
    assert changes["order"] == ["filter-2"]
    assert changes["moved"] == []


def test_stage_delete_works_without_order_or_moved():
    changes = empty_changes()

    stage_delete(changes, "filter-1")

    assert changes == {**empty_changes(), "deleted": ["filter-1"]}


def test_require_editable_row_allows_created_and_saved_rows(superuser, baseline_by_key):
    changes = empty_changes()
    key = stage_create(changes, "filter", filter_fields("x"))

    require_editable_row(superuser, key, baseline_by_key, changes, "filter")
    require_editable_row(superuser, "filter-1", baseline_by_key, changes, "filter")


def test_require_editable_row_rejects_a_missing_row(superuser, baseline_by_key):
    with pytest.raises(DraftError, match=r"^Filter not found\. Refresh the page and try again\.$"):
        require_editable_row(superuser, "filter-99", baseline_by_key, empty_changes(), "filter")


def test_require_editable_row_rejects_a_deleted_row(superuser, baseline_by_key):
    changes = {**empty_changes(), "deleted": ["filter-1"]}

    with pytest.raises(DraftError, match=r"^Filter not found\."):
        require_editable_row(superuser, "filter-1", baseline_by_key, changes, "filter")


def test_require_editable_row_needs_write_access(reader, baseline_by_key):
    with pytest.raises(PermissionDenied, match=r"^You do not have permission to modify this filter\.$"):
        require_editable_row(reader, "filter-1", baseline_by_key, empty_changes(), "filter")


def test_require_rows_still_exist_passes_for_saved_rows(superuser, baseline_by_key):
    changes = {**empty_changes(), "updated": {"filter-1": filter_fields("edited")}, "deleted": ["filter-2"]}

    require_rows_still_exist(superuser, changes, baseline_by_key, "filter")


def test_require_rows_still_exist_names_an_updated_row_deleted_by_someone_else(superuser, baseline_by_key):
    changes = {**empty_changes(), "updated": {"filter-99": filter_fields("gone")}}

    with pytest.raises(DraftError, match=r"^Filter 'gone' was deleted by someone else\. Discard your changes"):
        require_rows_still_exist(superuser, changes, baseline_by_key, "filter")


def test_require_rows_still_exist_uses_the_key_for_a_deleted_row(superuser, baseline_by_key):
    changes = {**empty_changes(), "deleted": ["filter-99"]}

    with pytest.raises(DraftError, match=r"^Filter 'filter-99' was deleted by someone else\."):
        require_rows_still_exist(superuser, changes, baseline_by_key, "filter")


def test_require_rows_still_exist_needs_write_access(reader, baseline_by_key):
    changes = {**empty_changes(), "deleted": ["filter-1"]}

    with pytest.raises(PermissionDenied, match=r"^You do not have permission to modify this filter\.$"):
        require_rows_still_exist(reader, changes, baseline_by_key, "filter")


def test_build_changeset_without_changes_is_all_unchanged(baseline):
    changeset = build_changeset(baseline, empty_changes(), FIELD_NAMES)

    assert [(entry["key"], entry["status"]) for entry in changeset] == [
        ("filter-1", "unchanged"),
        ("filter-2", "unchanged"),
    ]


def test_build_changeset_lists_saved_rows_then_created_rows(baseline):
    changes = empty_changes()
    stage_create(changes, "filter", filter_fields("new"))
    changes["updated"]["filter-1"] = filter_fields("a", description="edited")
    changes["deleted"].append("filter-2")

    changeset = build_changeset(baseline, changes, FIELD_NAMES)

    assert changeset == [
        {
            "key": "filter-1",
            "status": "changed",
            "fields": filter_fields("a", description="edited"),
            "previous_fields": filter_fields("a"),
            "changed_fields": ["description"],
            "enable_changed": False,
        },
        {
            "key": "filter-2",
            "status": "removed",
            "fields": filter_fields("b"),
            "previous_fields": filter_fields("b"),
            "changed_fields": [],
            "enable_changed": False,
        },
        {
            "key": "filterdraft-1",
            "status": "added",
            "fields": filter_fields("new"),
            "previous_fields": None,
            "changed_fields": [],
            "enable_changed": False,
        },
    ]


def test_build_changeset_reports_enable_separately(baseline):
    changes = {**empty_changes(), "updated": {"filter-1": filter_fields("a", enable=False)}}

    entry = build_changeset(baseline, changes, FIELD_NAMES)[0]

    assert entry["status"] == "changed"
    assert entry["changed_fields"] == []
    assert entry["enable_changed"] is True


def test_build_changeset_ignores_enable_when_it_is_not_a_field(baseline):
    changes = {**empty_changes(), "updated": {"filter-1": filter_fields("a", enable=False)}}

    entry = build_changeset(baseline, changes, ("name", "description"))[0]

    assert entry["status"] == "unchanged"
    assert entry["enable_changed"] is False
