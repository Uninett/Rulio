import pytest
from django.contrib.auth import get_user_model

from backend.objects.draft import Draft
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.draft import (
    changes_pending,
    discard_draft,
    empty_changes,
    get_changes,
    is_new_key,
    key_type,
    new_key,
    saved_key,
    store_changes,
)


@pytest.fixture
def draft_owner(superuser, create_testing_tenant):
    return {"actor": superuser, "tenant_id": create_testing_tenant.id}


def changes_with_created(name, object_type="filter"):
    changes = empty_changes()
    changes["created"][new_key(object_type, changes)] = {"name": name}
    return changes


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
