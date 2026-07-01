from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User

from backend.objects.filters.filter import Filter
from backend.objects.filters.rule_filter import RuleFilter
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.filters.rule import Rule
from backend.services.generate_config import Policy, PolicyRule
from backend.utils.logger import set_up_logger
from backend.services.get import get_platform_from_device
from backend.services.helper_user_tenant import is_superadmin, require_read_tenant


# Setup logger
logger = set_up_logger(__name__)


def create_tenant_user_member(
    *,
    actor: User,
    tenant_id: int,
    user_id: int,
    role: str,
) -> TenantUserMember:
    if not actor.is_authenticated:
        raise PermissionDenied("Authentication required.")

    if not is_superadmin(actor):
        raise PermissionDenied("Only superadmins can add tenant privileges to users.")

    tenant_user = TenantUserMember.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
    )
    logger.info(f"TenantUserMember created by {actor.username}: {tenant_user}")
    return tenant_user


"""
====================================================================
POLICY GENERATION
====================================================================
"""


def create_policy_rule_from_rule_match(
    *, actor: User, tenant_id: int, rule_match: RuleMatch, rule_sequence: int
) -> PolicyRule:
    require_read_tenant(actor, tenant_id)
    rule = rule_match.rule
    obj = rule_match.object
    if not obj:
        raise ValueError(f"Object with ID {rule_match.object_id} does not exist for rule with ID {rule.id}.")
    model_name = rule_match.object_type.model

    if model_name not in ["address", "service", "addressgroup", "servicegroup"]:
        raise ValueError(f"Invalid object type {rule_match.object_type} for rule with ID {rule.id}.")

    policy_rule = PolicyRule(
        actor=actor,
        tenant_id=tenant_id,
        name=rule.name,
        obj_type=model_name,
        action=rule.action,
        object=obj,
        rule_sequence=rule_sequence,
        direction=rule_match.match,
    )
    return policy_rule


def create_policy_rules_from_rule_filter(*, actor: User, tenant_id: int, rule_filter: RuleFilter) -> list[PolicyRule]:
    require_read_tenant(actor, tenant_id)
    policy_rules = []
    if not rule_filter.rule.id:
        raise ValueError(f"Rule with ID {rule_filter.rule.id} does not exist.")
    # Get rule_sequence from RuleFilter
    rule_sequence = rule_filter.rule_sequence
    if not rule_sequence:
        raise ValueError(f"Rule sequence is not set for rule match with ID {rule_filter.id}.")

    # Get actual rule object from join on RuleFilter
    rule = Rule.objects.get(id=rule_filter.rule.id)
    if not rule:
        raise ValueError(f"Rule with ID {rule_filter.rule.id} does not exist.")

    # Join rule with objects using RuleMatch to retrieve the actual rules
    rule_matches = RuleMatch.objects.filter(rule=rule)
    if not rule_matches.exists():
        raise ValueError(f"No rule matches found for rule with ID {rule.id}.")
    for rule_match in rule_matches:
        policy_rules.append(
            create_policy_rule_from_rule_match(
                actor=actor, tenant_id=tenant_id, rule_match=rule_match, rule_sequence=rule_sequence
            )
        )
    return policy_rules


def create_policy_from_filter(*, actor: User, tenant_id: int, filter_id, policy_sequence, vendor, policy_type):
    require_read_tenant(actor, tenant_id)

    # Get filter object by ID
    filter = Filter.objects.get(id=filter_id)
    if not filter:
        raise ValueError(f"Filter with ID {filter_id} does not exist.")

    # Join filter with rules using RuleFilter
    rule_filter_matches = RuleFilter.objects.filter(filter_id=filter)
    if not rule_filter_matches.exists():
        raise ValueError(f"No rule matches found for filter with ID {filter_id}.")

    # Create PolicyRule objects for each rule
    policy_rules = []
    for rule_filter in rule_filter_matches:
        policy_rules.extend(
            create_policy_rules_from_rule_filter(actor=actor, tenant_id=tenant_id, rule_filter=rule_filter)
        )

    policy = Policy(
        actor=actor,
        tenant_id=tenant_id,
        name=filter.name,
        rules=policy_rules,
        vendor=vendor,
        policy_type=policy_type,
        policy_sequence=policy_sequence,
    )
    return policy


def create_policies_for_interface(*, actor: User, tenant_id: int, interface_id, policy_type=""):
    require_read_tenant(actor, tenant_id)

    # Get interface object by ID
    interface = Interface.objects.get(id=interface_id)
    if not interface:
        raise ValueError(f"Interface with ID {interface_id} does not exist.")

    # Get the vendor/platform from the device associated with the interface
    vendor = get_platform_from_device(actor, tenant_id, interface.device_id)

    # Join interface on filters using FilterInterface, then sort filters by policy_sequence
    filter_interfaces = FilterInterface.objects.filter(interface_id=interface).order_by("policy_sequence")
    if not filter_interfaces.exists():
        raise ValueError(f"No filters found for interface with ID {interface_id}.")

    # Create Policy objects for each filter
    policies = []
    for filter_interface in filter_interfaces:
        filter_obj = Filter.objects.get(id=filter_interface.filter_id)
        if not filter_obj:
            raise ValueError(f"Filter with ID {filter_interface.filter_id} does not exist.")
        policy = create_policy_from_filter(
            actor=actor,
            tenant_id=tenant_id,
            filter_id=filter_obj.id,
            policy_sequence=filter_interface.policy_sequence,
            vendor=vendor,
            policy_type=policy_type,
        )
        policies.append(policy)
    logger.info(f"Created {len(policies)} policies for interface id={interface_id}")
    logger.info(f"Policies: {[policy.YAMLConfig for policy in policies]}")

    return policies
