import pytest
import yaml

from backend.services.filter_objects.create_filter_objects import create_filter
from backend.services.membership import (
    add_filter_to_interface,
    add_objects_to_rule,
)
from backend.services.config_generation.generate_config import generate_config, generate_multi_policy_config, merge_policies
from backend.services.tenant_objects.create_tenant_objects import create_device, create_interface
from backend.services.update import update_rule
from backend.utils.logger import set_up_logger
from backend.utils.write_to_file import write_configuration_to_file
from backend.services.config_generation.build import build_policies_for_interface, build_policy_from_filter
from constants import TEST_LOGPATH

logger = set_up_logger(__name__)


@pytest.mark.django_db
class TestGenerateConfigFromFilterObject:
    def test_generate_config_from_simple_filter_object(
        self, sample_filters, sample_rules, request_with_session, create_testing_tenant, sample_addresses
    ):
        update_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=sample_rules[0].id,
            filter=sample_filters[0],
        )

        response = add_objects_to_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=sample_rules[0].id,
            match_type="source",
            objects=[sample_addresses[0]],
        )
        if response["error_count"] > 0:
            logger.error(f"Error adding objects to rule: {response['errors']}")
        assert response["error_count"] == 0
        assert response["added_count"] > 0
        logger.info(f"Matched rule {sample_rules[0].id} to filter {sample_filters[0].id}, response:\n{response}")

        vendor = "juniper"
        policy = build_policy_from_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            filter_id=sample_filters[0].id,
            policy_sequence=10,
            vendor=vendor,
            policy_type="",
        )
        assert policy is not None

        config = generate_config(policy)

        filepath = TEST_LOGPATH / "from_filter" / f"{vendor.upper()}_simple_generated_config.yaml"
        filedir = TEST_LOGPATH / "from_filter"
        write_configuration_to_file(config, filepath, filedir, vendor, __name__)

    def test_generate_config_from_complex_filter_object(
        self,
        sample_filters,
        sample_rules,
        request_with_session,
        realistic_acl_addresses,
        realistic_acl_services,
        realistic_acl_address_groups,
        realistic_acl_service_groups,
    ):
        filter_id = sample_filters[1].id
        rules = [
            sample_rules[0].id,
            sample_rules[1].id,
            sample_rules[2].id,
            sample_rules[3].id,
        ]

        for i, rule_id in enumerate(rules):
            update_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rule_id,
                filter=sample_filters[1],
                rule_sequence=i + 1,
            )
            logger.info(
                f"Added rule {rule_id} to filter {filter_id} with rule_sequence {i + 1}, response:\n{update_rule.__name__}"
            )

        responses = [
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[0],
                match_type="source",
                objects=realistic_acl_addresses,
            ),
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[1],
                match_type="destination",
                objects=realistic_acl_services,
            ),
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[2],
                match_type="source",
                objects=realistic_acl_address_groups,
            ),
            add_objects_to_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rules[3],
                match_type="destination",
                objects=realistic_acl_service_groups,
            ),
        ]
        assert all(response["error_count"] == 0 for response in responses)

        vendor = "juniper"
        policy = build_policy_from_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            filter_id=sample_filters[1].id,
            policy_sequence=10,
            vendor=vendor,
            policy_type="",
        )
        assert policy is not None

        filepath = TEST_LOGPATH / "from_filter" / f"{vendor.upper()}_complex_generated_config.yaml"
        filedir = TEST_LOGPATH / "from_filter"
        config = generate_config(policy)
        write_configuration_to_file(config, filepath, filedir, vendor, __name__)

    def test_generate_config_from_interface(
        self,
        request_with_session,
        sample_rules_with_objects,
        sample_filters,
    ):
        new_filter = create_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name="Test Filter for Interface",
            description="This is a test filter for interface",
        )
        update_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=sample_rules_with_objects[1].id,
            filter=new_filter,
            rule_sequence=1,
        )

        interfaces = []
        for vendor in ["juniper", "cisco"]:
            device = create_device(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name=f"{vendor.upper()}_Test_Device",
                description="This is a test device",
                platform=vendor,
                type="firewall",
            )
            interface = create_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                name=f"{vendor.upper()}_Test_Interface",
                description="This is a test interface",
                type="ethernet",
                device_id=device.id,
                VRF=None,
            )
            interfaces.append(interface)

            add_filter_to_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=interface.id,
                filter_id=new_filter.id,
                policy_sequence=5,
                enable=False,
                direction="in",
            )
            add_filter_to_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=interface.id,
                filter_id=sample_filters[0].id,
                policy_sequence=10,
                enable=True,
                direction="in",
            )
            add_filter_to_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=interface.id,
                filter_id=sample_filters[1].id,
                policy_sequence=20,
                enable=True,
                direction="in",
            )

            policies = build_policies_for_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=interface.id,
                policy_type="",
                direction="in",
            )
            assert len(policies) == 2
            assert policies[0].policy_sequence == 10
            assert policies[1].policy_sequence == 20

            YAML1 = policies[0].YAMLConfig
            YAML2 = policies[1].YAMLConfig
            terms1 = YAML1["filters"][0]["terms"]
            terms2 = YAML2["filters"][0]["terms"]

            assert len(terms1) == 1
            assert len(terms2) == 1
            assert terms1[0]["name"] == sample_rules_with_objects[1].name.replace(" ", "_")[:62]
            assert terms2[0]["name"] == sample_rules_with_objects[2].name.replace(" ", "_")[:62]

            merged_policy = merge_policies(policies, name=None)
            assert merged_policy is not None
            logger.info(
                "Generated policy YAML:\n%s",
                yaml.dump(merged_policy.YAMLConfig, sort_keys=False, default_flow_style=False),
            )

            config = generate_multi_policy_config(policies)
            logger.info(
                "config.keys(): %s",
                config.keys(),
            )
            assert config is not None

            filepath = TEST_LOGPATH / "interface" / f"{interface.name}_generated_config.yaml"
            filedir = TEST_LOGPATH / "interface"
            write_configuration_to_file(
                config, filepath, filedir, device.platform, __name__, log_for_vendors=["juniper", "cisco"]
            )