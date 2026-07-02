from django.contrib.auth.models import User

from backend.objects.filters.rule import Rule
from backend.services.filter_objects.create_filter_objects import get_or_create_rule
from backend.services.membership import add_objects_to_rule
from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def seed_rules(
    *,
    actor: User,
    tenant_id: int,
    seeded_addresses,
    seeded_address_groups,
    seeded_services,
    seeded_service_groups,
) -> tuple[int, list[Rule]]:
    default_rules = []

    address_groups_by_name = {group.name: group for group in seeded_address_groups}
    services_by_name = {service.name: service for service in seeded_services}
    service_groups_by_name = {group.name: group for group in seeded_service_groups}

    rule_1, created_1 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Common_Infrastructure_Client_Services",
        description="Allow traffic from private and local use addresses to common infrastructure client services.",
        action="allow",
        log_type="none",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_1.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_1.id,
        match_type="destination",
        objects=[service_groups_by_name["Common_Infrastructure_Client_Services"]],
    )
    default_rules.append((rule_1, created_1))

    rule_2, created_2 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Common_Web_Access_Services",
        description="Allow traffic from private and local use addresses to common web access services.",
        action="allow",
        log_type="none",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_2.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_2.id,
        match_type="destination",
        objects=[service_groups_by_name["Common_Web_Access_Services"]],
    )
    default_rules.append((rule_2, created_2))

    rule_3, created_3 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Restricted_Administrative_Access_Services",
        description="Allow traffic from private and local use addresses to restricted administrative access services.",
        action="allow",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_3.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_3.id,
        match_type="destination",
        objects=[service_groups_by_name["Restricted_Administrative_Access_Services"]],
    )
    default_rules.append((rule_3, created_3))

    rule_4, created_4 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Restricted_Internal_Identity_Services",
        description="Allow traffic from private and local use addresses to restricted internal identity services.",
        action="allow",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_4.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_4.id,
        match_type="destination",
        objects=[service_groups_by_name["Restricted_Internal_Identity_Services"]],
    )
    default_rules.append((rule_4, created_4))

    rule_5, created_5 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Restricted_Internal_File_Sharing_Services",
        description="Allow traffic from private and local use addresses to restricted internal file sharing services.",
        action="allow",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_5.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_5.id,
        match_type="destination",
        objects=[service_groups_by_name["Restricted_Internal_File_Sharing_Services"]],
    )
    default_rules.append((rule_5, created_5))

    rule_6, created_6 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Restricted_Database_Services",
        description="Allow traffic from private and local use addresses to restricted database services.",
        action="allow",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_6.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_6.id,
        match_type="destination",
        objects=[service_groups_by_name["Restricted_Database_Services"]],
    )
    default_rules.append((rule_6, created_6))

    rule_7, created_7 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Allow_Private_And_Local_Use_Addresses_To_Restricted_Monitoring_And_Logging_Services",
        description="Allow traffic from private and local use addresses to restricted monitoring and logging services.",
        action="allow",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_7.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_7.id,
        match_type="destination",
        objects=[service_groups_by_name["Restricted_Monitoring_And_Logging_Services"]],
    )
    default_rules.append((rule_7, created_7))

    rule_8, created_8 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Invalid_Transit_Addresses_To_Any_TCP",
        description="Deny traffic from invalid transit addresses to any TCP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_8.id,
        match_type="source",
        objects=[address_groups_by_name["Invalid_Transit_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_8.id,
        match_type="destination",
        objects=[services_by_name["Any_TCP"]],
    )
    default_rules.append((rule_8, created_8))

    rule_9, created_9 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Invalid_Transit_Addresses_To_Any_UDP",
        description="Deny traffic from invalid transit addresses to any UDP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_9.id,
        match_type="source",
        objects=[address_groups_by_name["Invalid_Transit_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_9.id,
        match_type="destination",
        objects=[services_by_name["Any_UDP"]],
    )
    default_rules.append((rule_9, created_9))

    rule_10, created_10 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Documentation_And_Test_Addresses_To_Any_TCP",
        description="Deny traffic from documentation and test addresses to any TCP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_10.id,
        match_type="source",
        objects=[address_groups_by_name["Documentation_And_Test_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_10.id,
        match_type="destination",
        objects=[services_by_name["Any_TCP"]],
    )
    default_rules.append((rule_10, created_10))

    rule_11, created_11 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Documentation_And_Test_Addresses_To_Any_UDP",
        description="Deny traffic from documentation and test addresses to any UDP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_11.id,
        match_type="source",
        objects=[address_groups_by_name["Documentation_And_Test_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_11.id,
        match_type="destination",
        objects=[services_by_name["Any_UDP"]],
    )
    default_rules.append((rule_11, created_11))

    rule_12, created_12 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Multicast_Addresses_To_Any_TCP",
        description="Deny traffic to multicast addresses over any TCP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_12.id,
        match_type="destination",
        objects=[address_groups_by_name["Multicast_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_12.id,
        match_type="destination",
        objects=[services_by_name["Any_TCP"]],
    )
    default_rules.append((rule_12, created_12))

    rule_13, created_13 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Multicast_Addresses_To_Any_UDP",
        description="Deny traffic to multicast addresses over any UDP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_13.id,
        match_type="destination",
        objects=[address_groups_by_name["Multicast_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_13.id,
        match_type="destination",
        objects=[services_by_name["Any_UDP"]],
    )
    default_rules.append((rule_13, created_13))

    rule_14, created_14 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_IPv6_Transition_And_Translation_Addresses_To_Any_TCP",
        description="Deny traffic to IPv6 transition and translation addresses over any TCP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_14.id,
        match_type="destination",
        objects=[address_groups_by_name["IPv6_Transition_And_Translation_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_14.id,
        match_type="destination",
        objects=[services_by_name["Any_TCP"]],
    )
    default_rules.append((rule_14, created_14))

    rule_15, created_15 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_IPv6_Transition_And_Translation_Addresses_To_Any_UDP",
        description="Deny traffic to IPv6 transition and translation addresses over any UDP service.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_15.id,
        match_type="destination",
        objects=[address_groups_by_name["IPv6_Transition_And_Translation_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_15.id,
        match_type="destination",
        objects=[services_by_name["Any_UDP"]],
    )
    default_rules.append((rule_15, created_15))

    rule_16, created_16 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Private_And_Local_Use_Addresses_To_Deny_Legacy_Insecure_Services",
        description="Deny traffic from private and local use addresses to legacy insecure services.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_16.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_16.id,
        match_type="destination",
        objects=[service_groups_by_name["Deny_Legacy_Insecure_Services"]],
    )
    default_rules.append((rule_16, created_16))

    rule_17, created_17 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Private_And_Local_Use_Addresses_To_Deny_Tunneling_And_VPN_Services",
        description="Deny traffic from private and local use addresses to tunneling and VPN services.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_17.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_17.id,
        match_type="destination",
        objects=[service_groups_by_name["Deny_Tunneling_And_VPN_Services"]],
    )
    default_rules.append((rule_17, created_17))

    rule_18, created_18 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Private_And_Local_Use_Addresses_To_Deny_Voice_And_Signaling_Services",
        description="Deny traffic from private and local use addresses to voice and signaling services.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_18.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_18.id,
        match_type="destination",
        objects=[service_groups_by_name["Deny_Voice_And_Signaling_Services"]],
    )
    default_rules.append((rule_18, created_18))

    rule_19, created_19 = get_or_create_rule(
        tenant_id=tenant_id,
        actor=actor,
        name="Deny_Private_And_Local_Use_Addresses_To_Deny_Local_Link_Resolution_Services",
        description="Deny traffic from private and local use addresses to local link resolution services.",
        action="deny",
        log_type="flow",
        hit_count=0,
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_19.id,
        match_type="source",
        objects=[address_groups_by_name["Private_And_Local_Use_Addresses"]],
    )
    add_objects_to_rule(
        actor=actor,
        tenant_id=tenant_id,
        rule_id=rule_19.id,
        match_type="destination",
        objects=[service_groups_by_name["Deny_Local_Link_Resolution_Services"]],
    )
    default_rules.append((rule_19, created_19))

    created_flags = [rule[1] for rule in default_rules]
    default_rules_count = len(default_rules)
    default_rules = [rule[0] for rule in default_rules]

    if all(created_flags):
        logger.info("All default rules were created. No duplicates existed.")
    elif any(created_flags):
        logger.warning("Some default rules already existed. Missing rules were created.")
    else:
        logger.warning("No default rules were created because they already all existed.")

    return default_rules_count, default_rules
