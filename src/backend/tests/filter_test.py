import pytest

from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.filters.versionControl import VersionControl
from backend.services.filter_objects.create_filter_objects import (
    create_filter,
    create_rule,
)
from backend.services.membership import copy_rule_to_filter


class TestFilters:
    def test_import_filters(self):
        # Test that imports work and we can use the classes
        assert Filter is not None
        assert Rule is not None
        assert RuleMatch is not None
        assert VersionControl is not None


def _create_filter_with_rule(actor, tenant_id, filter_name):
    filter_obj = create_filter(actor=actor, tenant_id=tenant_id, name=filter_name, description="")
    rule = create_rule(
        actor=actor,
        filter=filter_obj,
        tenant_id=tenant_id,
        name="copied-rule",
        description="",
        action="accept",
        enable=True,
        log_type="None",
        hit_count=0,
    )
    return filter_obj, rule


def test_copy_rule_to_filter_keeps_the_rule_name(superuser, create_testing_tenant):
    _source_filter, rule = _create_filter_with_rule(superuser, create_testing_tenant.id, "Copy source filter")
    target_filter = create_filter(
        actor=superuser, tenant_id=create_testing_tenant.id, name="Copy target filter", description=""
    )

    copy = copy_rule_to_filter(
        actor=superuser,
        tenant_id=create_testing_tenant.id,
        rule_id=rule.id,
        filter_id=target_filter.id,
        rule_sequence=1,
    )

    assert copy.name == "copied-rule"
    assert copy.filter_id == target_filter.id


def test_copy_rule_to_filter_rejects_a_name_already_in_the_filter(superuser, create_testing_tenant):
    source_filter, rule = _create_filter_with_rule(superuser, create_testing_tenant.id, "Copy source filter")

    with pytest.raises(ValueError):
        copy_rule_to_filter(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            rule_id=rule.id,
            filter_id=source_filter.id,
            rule_sequence=2,
        )

    assert Rule.objects.filter(filter=source_filter).count() == 1
