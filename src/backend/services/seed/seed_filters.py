

from django.contrib.auth.models import User

from backend.objects.filters.rule import Rule
from backend.objects.filters.filter import Filter
from backend.services.filter_objects.create_filter_objects import get_or_create_filter
from backend.services.membership import add_rule_to_filter

from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def seed_filters(
    *,
    actor: User,
    tenant_id: int,
    seeded_rules: list[Rule],
) -> tuple[int, list[Filter]]:
    default_filters = []

    rules_by_name = {rule.name: rule for rule in seeded_rules}

    filter_1, created_1 = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Baseline_Internal_Client_Policy",
        description="Baseline internal client policy allowing common business traffic and denying risky categories.",
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Invalid_Transit_Addresses_To_Any_TCP"].id,
        filter_id=filter_1.id,
        rule_sequence=10,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Invalid_Transit_Addresses_To_Any_UDP"].id,
        filter_id=filter_1.id,
        rule_sequence=20,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Documentation_And_Test_Addresses_To_Any_TCP"].id,
        filter_id=filter_1.id,
        rule_sequence=30,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Documentation_And_Test_Addresses_To_Any_UDP"].id,
        filter_id=filter_1.id,
        rule_sequence=40,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Multicast_Addresses_To_Any_TCP"].id,
        filter_id=filter_1.id,
        rule_sequence=50,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Multicast_Addresses_To_Any_UDP"].id,
        filter_id=filter_1.id,
        rule_sequence=60,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Common_Infrastructure_Client_Services"].id,
        filter_id=filter_1.id,
        rule_sequence=100,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Common_Web_Access_Services"].id,
        filter_id=filter_1.id,
        rule_sequence=110,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Legacy_Insecure_Services"].id,
        filter_id=filter_1.id,
        rule_sequence=200,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Tunneling_And_VPN_Services"].id,
        filter_id=filter_1.id,
        rule_sequence=210,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Voice_And_Signaling_Services"].id,
        filter_id=filter_1.id,
        rule_sequence=220,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Local_Link_Resolution_Services"].id,
        filter_id=filter_1.id,
        rule_sequence=230,
    )
    default_filters.append((filter_1, created_1))

    filter_2, created_2 = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Internal_Server_Policy",
        description="Internal server policy allowing management, identity, database, file sharing, and monitoring services for private networks.",
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Invalid_Transit_Addresses_To_Any_TCP"].id,
        filter_id=filter_2.id,
        rule_sequence=10,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Invalid_Transit_Addresses_To_Any_UDP"].id,
        filter_id=filter_2.id,
        rule_sequence=20,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Multicast_Addresses_To_Any_TCP"].id,
        filter_id=filter_2.id,
        rule_sequence=30,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Multicast_Addresses_To_Any_UDP"].id,
        filter_id=filter_2.id,
        rule_sequence=40,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Restricted_Administrative_Access_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=100,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Restricted_Internal_Identity_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=110,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Restricted_Internal_File_Sharing_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=120,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Restricted_Database_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=130,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Restricted_Monitoring_And_Logging_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=140,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Legacy_Insecure_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=200,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Tunneling_And_VPN_Services"].id,
        filter_id=filter_2.id,
        rule_sequence=210,
    )
    default_filters.append((filter_2, created_2))

    filter_3, created_3 = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Strict_Egress_Policy",
        description="Strict egress policy for private address space allowing only core infrastructure and web access while denying common risky categories.",
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Invalid_Transit_Addresses_To_Any_TCP"].id,
        filter_id=filter_3.id,
        rule_sequence=10,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Invalid_Transit_Addresses_To_Any_UDP"].id,
        filter_id=filter_3.id,
        rule_sequence=20,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Documentation_And_Test_Addresses_To_Any_TCP"].id,
        filter_id=filter_3.id,
        rule_sequence=30,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Documentation_And_Test_Addresses_To_Any_UDP"].id,
        filter_id=filter_3.id,
        rule_sequence=40,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_IPv6_Transition_And_Translation_Addresses_To_Any_TCP"].id,
        filter_id=filter_3.id,
        rule_sequence=50,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_IPv6_Transition_And_Translation_Addresses_To_Any_UDP"].id,
        filter_id=filter_3.id,
        rule_sequence=60,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Legacy_Insecure_Services"].id,
        filter_id=filter_3.id,
        rule_sequence=70,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Tunneling_And_VPN_Services"].id,
        filter_id=filter_3.id,
        rule_sequence=80,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Voice_And_Signaling_Services"].id,
        filter_id=filter_3.id,
        rule_sequence=90,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Deny_Private_And_Local_Use_Addresses_To_Deny_Local_Link_Resolution_Services"].id,
        filter_id=filter_3.id,
        rule_sequence=100,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Common_Infrastructure_Client_Services"].id,
        filter_id=filter_3.id,
        rule_sequence=200,
    )
    add_rule_to_filter(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rules_by_name["Allow_Private_And_Local_Use_Addresses_To_Common_Web_Access_Services"].id,
        filter_id=filter_3.id,
        rule_sequence=210,
    )
    default_filters.append((filter_3, created_3))

    created_flags = [filter_obj[1] for filter_obj in default_filters]
    default_filter_count = len(default_filters)
    default_filters = [filter_obj[0] for filter_obj in default_filters]

    if all(created_flags):
        logger.info("All default filters were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default filters already existed. Missing filters were created.")
    else:
        logger.warning("No default filters were created because they already all existed.")

    return default_filter_count, default_filters


