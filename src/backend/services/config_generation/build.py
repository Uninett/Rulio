from django.contrib.auth.models import User

from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.filters.rule_match import RuleMatch
from backend.objects.tenant_objects.filter_interface import FilterInterface
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.interface_direction import InterfaceDirection
from backend.services.config_generation.generate_config import Policy, PolicyRule, PolicyRuleMember
from backend.services.get import get_platform_from_device
from backend.services.helper_user_tenant import require_read_tenant
from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def build_policy_rule_member_from_rule_match(*, rule_match: RuleMatch) -> PolicyRuleMember:
    """
    Build a PolicyRuleMember from a RuleMatch.
    """
    obj = rule_match.object
    if not obj:
        raise ValueError(f"Object with ID {rule_match.object_id} does not exist for rule with ID {rule_match.rule.id}.")

    model_name = rule_match.object_type.model
    if model_name not in {"address", "service", "addressgroup", "servicegroup"}:
        raise ValueError(f"Invalid object type {rule_match.object_type} for rule with ID {rule_match.rule.id}.")

    return PolicyRuleMember(
        obj_type=model_name,
        direction=rule_match.match,
        object=obj,
    )


def build_policy_rule_from_rule(
    *,
    actor: User,
    tenant_id: int,
    rule: Rule,
) -> PolicyRule:
    """
    Build a single PolicyRule from a Rule.

    One Rule corresponds to one logical PolicyRule.
    All related RuleMatch rows are converted into PolicyRuleMember objects.
    """
    require_read_tenant(actor, tenant_id)

    if not rule:
        raise ValueError("Rule does not exist.")

    if rule.enable is False:
        raise ValueError(f"Rule with ID {rule.id} is disabled and cannot be built.")

    if rule.rule_sequence is None:
        raise ValueError(f"Rule sequence is not set for rule with ID {rule.id}.")

    rule_matches = RuleMatch.objects.filter(rule=rule)
    if not rule_matches.exists():
        raise ValueError(f"No rule matches found for rule with ID {rule.id}.")

    members = [build_policy_rule_member_from_rule_match(rule_match=rule_match) for rule_match in rule_matches]

    return PolicyRule(
        actor=actor,
        tenant_id=tenant_id,
        name=rule.name,
        action=rule.action,
        rule_sequence=rule.rule_sequence,
        members=members,
    )


def build_policy_from_filter(
    *,
    actor: User,
    tenant_id: int,
    filter_id: int,
    policy_sequence: int,
    vendor: str,
    target_spec: str = "",
) -> Policy:
    """
    Build a Policy from a Filter and its enabled Rule rows.
    """
    require_read_tenant(actor, tenant_id)

    filter_obj = Filter.objects.get(id=filter_id)

    rules = Rule.objects.filter(filter_id=filter_obj.id).order_by("rule_sequence")
    if not rules.exists():
        raise ValueError(f"No rules found for filter with ID {filter_id}.")

    policy_rules = []
    for rule in rules:
        if rule.enable is False:
            logger.info(f"Skipping disabled rule with ID {rule.id} for filter with ID {filter_id}.")
            continue

        policy_rules.append(
            build_policy_rule_from_rule(
                actor=actor,
                tenant_id=tenant_id,
                rule=rule,
            )
        )

    return Policy(
        actor=actor,
        tenant_id=tenant_id,
        name=filter_obj.name,
        rules=policy_rules,
        vendor=vendor,
        target_spec=target_spec,
        policy_sequence=policy_sequence,
    )


def build_policies_for_interface(
    *,
    actor: User,
    tenant_id: int,
    interface_id: int,
    direction: str,
    target_spec: str = "",
) -> list[Policy]:
    """
    Build Policy objects for all enabled filters attached to an interface direction.
    """
    require_read_tenant(actor, tenant_id)

    if direction not in ["in", "out"]:
        raise ValueError(f"Invalid direction '{direction}' specified. Must be 'in' or 'out'.")

    interface = Interface.objects.get(id=interface_id)

    vendor = get_platform_from_device(
        actor=actor,
        tenant_id=tenant_id,
        device_id=interface.device_id,
    )

    interface_direction = InterfaceDirection.objects.get(interface=interface, direction=direction)

    filter_interfaces = FilterInterface.objects.filter(interface_direction_id=interface_direction.id).order_by(
        "policy_sequence"
    )
    if not filter_interfaces.exists():
        raise ValueError(f"No filters found for interface with ID {interface_id} for direction '{direction}'.")

    policies = []
    for filter_interface in filter_interfaces:
        if filter_interface.enable is False:
            logger.info(
                f"Skipping disabled filter_interface with ID {filter_interface.id} "
                f"for interface with ID {interface_id} and direction '{direction}'."
            )
            continue

        filter_obj = Filter.objects.get(id=filter_interface.filter_id)

        policy = build_policy_from_filter(
            actor=actor,
            tenant_id=tenant_id,
            filter_id=filter_obj.id,
            policy_sequence=filter_interface.policy_sequence,
            vendor=vendor,
            target_spec=target_spec,
        )
        policies.append(policy)

    logger.info(f"Built {len(policies)} policies for interface id={interface_id} direction='{direction}'")
    logger.info(f"Policies: {[policy.YAMLConfig for policy in policies]}")

    return policies
