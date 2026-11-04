import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from backend.objects.attributes.tag import Tag
from backend.objects.draft import Draft
from backend.objects.filters.filter import Filter
from backend.objects.tenant_objects.tenant import Tenant
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.services.attribute_objects.create_attribute_objects import create_tag
from backend.services.draft import store_changes
from backend.services.filter_draft import (
    FILTER_DRAFT_SCOPE,
    FILTER_DRAFT_SCOPE_ID,
    FilterDraftError,
    apply_filter_draft,
    build_filter_changeset,
    discard_filter_draft,
    filter_changes_pending,
    get_filter_changes,
    load_baseline_filters,
    saved_filter_key,
    stage_filter_create,
    stage_filter_delete,
    stage_filter_update,
)
from backend.services.filter_objects.create_filter_objects import (
    create_filter,
    create_rule,
)
from backend.services.rule_draft import RULE_DRAFT_SCOPE, stage_rule_create
from constants import GLOBAL_TENANT_ID


def filter_fields(name, **overrides):
    return {"name": name, "description": "", "tag_ids": [], **overrides}


# A normal tenant, so filters in the global tenant can be told apart from the tenant's own.
@pytest.fixture
def filter_tenant(db, create_testing_tenant):
    return Tenant.objects.create(tenant_name="Filter draft tenant")


@pytest.fixture
def saved_filters(superuser, filter_tenant):
    return [
        create_filter(actor=superuser, tenant_id=filter_tenant.id, name=name, description="")
        for name in ("draft-filter-a", "draft-filter-b")
    ]


@pytest.fixture
def draft_args(superuser, filter_tenant, saved_filters):
    return {"actor": superuser, "tenant_id": filter_tenant.id}


def changeset_for(draft_args):
    baseline = load_baseline_filters(draft_args["actor"], draft_args["tenant_id"])
    return build_filter_changeset(baseline, get_filter_changes(draft_args["actor"], draft_args["tenant_id"]))


def entry_for(changeset, key):
    return next(entry for entry in changeset if entry["key"] == key)


def has_filter_draft(actor):
    return Draft.objects.filter(user=actor, scope=FILTER_DRAFT_SCOPE).exists()


def test_staged_create_is_not_saved_until_draft_is_applied(draft_args):
    new_key = stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new"))

    assert new_key == "filterdraft-1"
    assert not Filter.objects.filter(name="draft-filter-new").exists()

    apply_filter_draft(**draft_args)

    assert Filter.objects.filter(name="draft-filter-new", tenant_id=draft_args["tenant_id"]).exists()
    assert not has_filter_draft(draft_args["actor"])


def test_changeset_marks_added_removed_and_changed_filters(draft_args, saved_filters):
    filter_a, filter_b = saved_filters
    key_a, key_b = saved_filter_key(filter_a.id), saved_filter_key(filter_b.id)
    new_key = stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new"))
    stage_filter_update(**draft_args, key=key_a, fields=filter_fields("draft-filter-a", description="edited"))
    stage_filter_delete(**draft_args, key=key_b)

    changeset = changeset_for(draft_args)

    assert entry_for(changeset, key_a)["status"] == "changed"
    assert entry_for(changeset, key_a)["changed_fields"] == ["description"]
    assert entry_for(changeset, key_b)["status"] == "removed"
    assert entry_for(changeset, new_key)["status"] == "added"
    assert Filter.objects.get(id=filter_a.id).description == ""
    assert Filter.objects.filter(id=filter_b.id).exists()


def test_editing_a_filter_back_to_its_saved_values_clears_the_draft(draft_args, saved_filters):
    key_a = saved_filter_key(saved_filters[0].id)
    stage_filter_update(**draft_args, key=key_a, fields=filter_fields("draft-filter-renamed"))
    stage_filter_update(**draft_args, key=key_a, fields=filter_fields("draft-filter-a"))

    assert not has_filter_draft(draft_args["actor"])


def test_deleting_a_filter_created_in_the_draft_drops_it(draft_args):
    new_key = stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new"))
    stage_filter_delete(**draft_args, key=new_key)

    assert not has_filter_draft(draft_args["actor"])


def test_a_filter_without_a_name_is_rejected(draft_args):
    with pytest.raises(FilterDraftError, match="Missing required fields."):
        stage_filter_create(**draft_args, fields=filter_fields(""))


def test_a_tag_from_another_tenant_is_rejected(superuser, draft_args):
    other_tenant = Tenant.objects.create(tenant_name="Other filter draft tenant")
    other_tag = create_tag(actor=superuser, tenant_id=other_tenant.id, name="other-tag", description="")

    with pytest.raises(FilterDraftError, match="Invalid tag selection."):
        stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new", tag_ids=[other_tag.id]))


def test_a_deleted_filter_can_not_be_edited(draft_args, saved_filters):
    key_a = saved_filter_key(saved_filters[0].id)
    stage_filter_delete(**draft_args, key=key_a)

    with pytest.raises(FilterDraftError, match="Filter not found."):
        stage_filter_update(**draft_args, key=key_a, fields=filter_fields("draft-filter-renamed"))


def test_apply_saves_creates_updates_and_deletes_with_tags(superuser, draft_args, saved_filters):
    filter_a, filter_b = saved_filters
    tag_one = create_tag(actor=superuser, tenant_id=draft_args["tenant_id"], name="filter-tag-1", description="")
    tag_two = create_tag(actor=superuser, tenant_id=draft_args["tenant_id"], name="filter-tag-2", description="")
    filter_a.add_tag(tag_one)

    stage_filter_update(
        **draft_args,
        key=saved_filter_key(filter_a.id),
        fields=filter_fields("draft-filter-renamed", description="new", tag_ids=[tag_two.id]),
    )
    stage_filter_delete(**draft_args, key=saved_filter_key(filter_b.id))
    stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new", tag_ids=[tag_one.id, tag_two.id]))

    apply_filter_draft(**draft_args)

    filter_a.refresh_from_db()
    assert (filter_a.name, filter_a.description) == ("draft-filter-renamed", "new")
    assert [tag.id for tag in filter_a.get_tags()] == [tag_two.id]
    assert not Filter.objects.filter(id=filter_b.id).exists()
    created = Filter.objects.get(name="draft-filter-new")
    assert sorted(tag.id for tag in created.get_tags()) == [tag_one.id, tag_two.id]
    assert not has_filter_draft(draft_args["actor"])


def test_apply_stops_when_a_filter_was_deleted_by_someone_else(draft_args, saved_filters):
    filter_a, filter_b = saved_filters
    stage_filter_update(**draft_args, key=saved_filter_key(filter_a.id), fields=filter_fields("draft-filter-renamed"))
    stage_filter_delete(**draft_args, key=saved_filter_key(filter_b.id))
    stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new"))
    Filter.objects.filter(id=filter_a.id).delete()

    with pytest.raises(FilterDraftError, match="was deleted by someone else"):
        apply_filter_draft(**draft_args)

    assert Filter.objects.filter(id=filter_b.id).exists()
    assert not Filter.objects.filter(name="draft-filter-new").exists()
    assert has_filter_draft(draft_args["actor"])


def test_deleting_a_filter_removes_rule_drafts_for_it(superuser, draft_args, saved_filters):
    filter_a, filter_b = saved_filters
    rule_fields = {
        "name": "draft-rule",
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
    other_user = get_user_model().objects.create_superuser(username="other-admin", password="x")
    for actor in (superuser, other_user):
        for filter_obj in (filter_a, filter_b):
            stage_rule_create(
                actor=actor, tenant_id=draft_args["tenant_id"], filter_id=filter_obj.id, fields=rule_fields
            )
    stage_filter_delete(**draft_args, key=saved_filter_key(filter_a.id))

    apply_filter_draft(**draft_args)

    assert not Draft.objects.filter(scope=RULE_DRAFT_SCOPE, scope_id=filter_a.id).exists()
    assert Draft.objects.filter(scope=RULE_DRAFT_SCOPE, scope_id=filter_b.id).count() == 2


def test_superuser_can_delete_a_global_filter_from_another_tenant(superuser, draft_args):
    global_filter = create_filter(actor=superuser, tenant_id=GLOBAL_TENANT_ID, name="global-filter", description="")
    create_rule(
        actor=superuser,
        filter=global_filter,
        tenant_id=GLOBAL_TENANT_ID,
        name="global-rule",
        description="",
        action="accept",
        enable=True,
        log_type="None",
        hit_count=0,
    )
    stage_filter_delete(**draft_args, key=saved_filter_key(global_filter.id))

    apply_filter_draft(**draft_args)

    assert not Filter.objects.filter(id=global_filter.id).exists()
    assert not has_filter_draft(draft_args["actor"])


def test_a_user_without_write_access_can_not_stage_or_save(filter_tenant, saved_filters):
    reader = get_user_model().objects.create_user(username="filter-draft-reader", password="x")

    with pytest.raises(PermissionDenied):
        stage_filter_create(actor=reader, tenant_id=filter_tenant.id, fields=filter_fields("draft-filter-new"))
    with pytest.raises(PermissionDenied):
        apply_filter_draft(actor=reader, tenant_id=filter_tenant.id)


def test_discard_removes_the_draft(draft_args, saved_filters):
    stage_filter_delete(**draft_args, key=saved_filter_key(saved_filters[0].id))

    discard_filter_draft(draft_args["actor"], draft_args["tenant_id"])

    assert not has_filter_draft(draft_args["actor"])
    assert not filter_changes_pending(get_filter_changes(draft_args["actor"], draft_args["tenant_id"]))


def test_a_name_longer_than_the_database_allows_is_rejected(draft_args):
    max_length = Filter._meta.get_field("name").max_length

    with pytest.raises(FilterDraftError, match=f"at most {max_length} characters"):
        stage_filter_create(**draft_args, fields=filter_fields("x" * (max_length + 1)))

    stage_filter_create(**draft_args, fields=filter_fields("x" * max_length))


def test_apply_stops_when_a_selected_tag_was_deleted(superuser, draft_args, saved_filters):
    filter_a, _filter_b = saved_filters
    tag = create_tag(actor=superuser, tenant_id=draft_args["tenant_id"], name="doomed-tag", description="")
    stage_filter_update(**draft_args, key=saved_filter_key(filter_a.id), fields=filter_fields("draft-filter-renamed"))
    stage_filter_create(**draft_args, fields=filter_fields("draft-filter-new", tag_ids=[tag.id]))
    Tag.objects.filter(id=tag.id).delete()

    with pytest.raises(FilterDraftError, match="A selected tag no longer exists."):
        apply_filter_draft(**draft_args)

    assert Filter.objects.get(id=filter_a.id).name == "draft-filter-a"
    assert not Filter.objects.filter(name="draft-filter-new").exists()
    assert has_filter_draft(draft_args["actor"])


def test_superuser_can_edit_a_global_filter_from_another_tenant(superuser, draft_args):
    global_filter = create_filter(actor=superuser, tenant_id=GLOBAL_TENANT_ID, name="global-filter", description="")
    # A global filter can only have global tags (TagConnection checks the tenants).
    tag = create_tag(actor=superuser, tenant_id=GLOBAL_TENANT_ID, name="global-tag", description="")
    stage_filter_update(
        **draft_args,
        key=saved_filter_key(global_filter.id),
        fields=filter_fields("global-filter-renamed", tag_ids=[tag.id]),
    )

    apply_filter_draft(**draft_args)

    global_filter.refresh_from_db()
    assert global_filter.name == "global-filter-renamed"
    assert global_filter.tenant_id == GLOBAL_TENANT_ID
    assert [found.id for found in global_filter.get_tags()] == [tag.id]


def test_a_tenant_admin_can_not_delete_a_global_filter(superuser, filter_tenant):
    tenant_admin = get_user_model().objects.create_user(username="filter-tenant-admin", password="x")
    TenantUserMember.objects.create(user=tenant_admin, tenant=filter_tenant, role=TenantUserMember.TenantRole.ADMIN)
    global_filter = create_filter(actor=superuser, tenant_id=GLOBAL_TENANT_ID, name="global-filter", description="")
    key = saved_filter_key(global_filter.id)

    with pytest.raises(PermissionDenied):
        stage_filter_delete(actor=tenant_admin, tenant_id=filter_tenant.id, key=key)

    # A draft that holds the deletion anyway (e.g. made before the user lost access) is refused when saving.
    changes = {**get_filter_changes(tenant_admin, filter_tenant.id), "deleted": [key]}
    store_changes(tenant_admin, filter_tenant.id, FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID, changes)
    with pytest.raises(PermissionDenied):
        apply_filter_draft(actor=tenant_admin, tenant_id=filter_tenant.id)

    assert Filter.objects.filter(id=global_filter.id).exists()


def test_a_tenant_tag_on_a_global_filter_is_rejected(superuser, draft_args):
    global_filter = create_filter(actor=superuser, tenant_id=GLOBAL_TENANT_ID, name="global-filter", description="")
    tag = create_tag(actor=superuser, tenant_id=draft_args["tenant_id"], name="tenant-tag", description="")

    with pytest.raises(FilterDraftError, match="A global filter can only have global tags."):
        stage_filter_update(
            **draft_args,
            key=saved_filter_key(global_filter.id),
            fields=filter_fields("global-filter", tag_ids=[tag.id]),
        )


def test_apply_reports_a_model_check_instead_of_crashing(superuser, draft_args, saved_filters):
    filter_a, _filter_b = saved_filters
    global_filter = create_filter(actor=superuser, tenant_id=GLOBAL_TENANT_ID, name="global-filter", description="")
    tag = create_tag(actor=superuser, tenant_id=draft_args["tenant_id"], name="tenant-tag", description="")
    stage_filter_update(**draft_args, key=saved_filter_key(filter_a.id), fields=filter_fields("draft-filter-renamed"))
    # Written directly, as staging refuses it: a tenant tag on a global filter, which the model check rejects.
    changes = get_filter_changes(**draft_args)
    changes["updated"][saved_filter_key(global_filter.id)] = filter_fields("global-filter", tag_ids=[tag.id])
    store_changes(draft_args["actor"], draft_args["tenant_id"], FILTER_DRAFT_SCOPE, FILTER_DRAFT_SCOPE_ID, changes)

    with pytest.raises(FilterDraftError, match="same tenant"):
        apply_filter_draft(**draft_args)

    assert Filter.objects.get(id=filter_a.id).name == "draft-filter-a"
    assert not global_filter.get_tags().exists()
    assert has_filter_draft(draft_args["actor"])
