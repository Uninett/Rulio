import datetime
import os
import yaml
import pytest

from backend.services.generate_config import generate_config, Policy
from backend.utils.logger import clear_logs, set_up_logger
from constants import TEST_LOGPATH


logger = set_up_logger(__name__)
clear_logs(__name__)


@pytest.mark.django_db
class TestGenerateConfig:
    vendor_policy_type_pairs = [
        ("juniper", ""),
        ("arista", ""),
        ("aruba", ""),
        ("cisco", "mixed"),
        ("brocade", ""),
        ("paloalto", ["from-zone", "internal", "to-zone", "external", "mixed"]),
    ]
    log_for_vendors = ["juniper"]
    def test_generate_address_config(self, address_policy_rules):

        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(name="Address_Test_Policy", rules=address_policy_rules, vendor=vendor, policy_type=policy_type)
            if vendor in self.log_for_vendors:
                logger.info(
                    "Generated policy YAML:\n%s",
                    yaml.dump(policy.YAMLConfig, sort_keys=False, default_flow_style=False),
                )
                logger.info(
                    "Generated networks:\n%s",
                    yaml.dump(policy.networks, sort_keys=False, default_flow_style=False),
                )

            assert policy.name == "Address_Test_Policy"
            assert policy.YAMLConfig["filename"] == "Address_Test_Policy"
            assert len(policy.YAMLConfig["filters"][0]["terms"]) == len(address_policy_rules)
            assert policy.YAMLConfig["filters"][0]["terms"][0]["name"] == "Test_Address_Rule_1"
            assert policy.YAMLConfig["filters"][0]["terms"][0]["destination-address"] == "Test_Address_1"
            assert policy.networks["networks"]["Test_Address_1"]["values"][0] == "192.168.1.0/24"
            assert policy.YAMLConfig["filters"][0]["terms"][0]["action"] == "accept"
            assert policy.YAMLConfig["filters"][0]["terms"][1]["name"] == "Test_Address_Rule_2"
            assert policy.YAMLConfig["filters"][0]["terms"][1]["source-address"] == "Test_Address_2"
            assert policy.YAMLConfig["filters"][0]["terms"][1]["action"] == "deny"

            config = generate_config(policy)
            filepath = TEST_LOGPATH / "addr" / f"{vendor.upper()}_generated_config.yaml"
            os.makedirs(TEST_LOGPATH / "addr", exist_ok=True)

            for filename, content in config.items():
                if vendor in self.log_for_vendors:
                    logger.info(
                        "\n=== Generated config: %s ===\n%s\n=== End config ===",
                        filename,
                        content,
                    )
                with open(filepath, "w") as f:
                    f.write(
                        f"# Generated on {datetime.datetime.now()}\n# Test for generating using only Address objects\n\n"
                    )
                    f.write(content)

    def test_generate_address_group_config(self, address_group_policy_rules, sample_addresses):
        
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(name="Address_Group_Test_Policy", rules=address_group_policy_rules, vendor=vendor, policy_type=policy_type)
            if vendor in self.log_for_vendors:
                logger.info(
                    "Generated policy YAML:\n%s",
                    yaml.dump(policy.YAMLConfig, sort_keys=False, default_flow_style=False),
                )
                logger.info(
                    "Generated networks:\n%s",
                    yaml.dump(policy.networks, sort_keys=False, default_flow_style=False),
                )

            assert policy.name == "Address_Group_Test_Policy"
            assert policy.YAMLConfig["filename"] == "Address_Group_Test_Policy"
            #assert policy.YAMLConfig["filters"][0]["header"]["targets"] == {vendor: f"Address_Group_Test_Policy {policy_type}"}
            assert len(policy.YAMLConfig["filters"][0]["terms"]) == len(address_group_policy_rules)
            assert policy.YAMLConfig["filters"][0]["terms"][0]["name"] == "Test_Rule_for_Address_Group_1"
            assert policy.YAMLConfig["filters"][0]["terms"][1]["name"] == "Test_Rule_for_Address_Group_2"

            config = generate_config(policy)
            filepath = TEST_LOGPATH / "addr_group" / f"{vendor.upper()}_generated_config.yaml"
            os.makedirs(TEST_LOGPATH / "addr_group", exist_ok=True)
            for filename, content in config.items():
                if vendor in self.log_for_vendors:
                    logger.info(
                        "\n=== Generated config: %s ===\n%s\n=== End config ===",
                        filename,
                        content,
                    )
                with open(filepath, "w") as f:
                    f.write(
                        f"# Generated on {datetime.datetime.now()}\n# Test for generating using Address Group objects\n\n"
                    )
                    f.write(content)

    def test_generate_service_config(self, service_policy_rules):
        
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(name="Service_Test_Policy", rules=service_policy_rules, vendor=vendor, policy_type=policy_type)
            if vendor in self.log_for_vendors:
                logger.info(
                    "Generated policy YAML:\n%s",
                    yaml.dump(policy.YAMLConfig, sort_keys=False, default_flow_style=False),
                )
                logger.info(
                    "Generated services:\n%s",
                    yaml.dump(policy.services, sort_keys=False, default_flow_style=False),
                )

            assert policy.name == "Service_Test_Policy"
            assert policy.YAMLConfig["filename"] == "Service_Test_Policy"
            #assert policy.YAMLConfig["filters"][0]["header"]["targets"] == {vendor: f"Service_Test_Policy {policy_type}"}
            assert len(policy.YAMLConfig["filters"][0]["terms"]) == len(service_policy_rules)
            assert policy.YAMLConfig["filters"][0]["terms"][0]["name"] == "Test_Service_Rule_1"
            assert policy.YAMLConfig["filters"][0]["terms"][1]["name"] == "Test_Service_Rule_2"

            config = generate_config(policy)
            filepath = TEST_LOGPATH / "service" / f"{vendor.upper()}_generated_config.yaml"
            os.makedirs(TEST_LOGPATH / "service", exist_ok=True)
            for filename, content in config.items():
                if vendor in self.log_for_vendors:
                    logger.info(
                        "\n=== Generated config: %s ===\n%s\n=== End config ===",
                        filename,
                        content,
                    )
                with open(filepath, "w") as f:
                    f.write(
                        f"# Generated on {datetime.datetime.now()}\n# Test for generating using Service objects\n\n"
                    )
                    f.write(content)

    def test_generate_service_group_config(self, service_group_policy_rules, sample_services):
        
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(name="Service_Group_Test_Policy", rules=service_group_policy_rules, vendor=vendor, policy_type=policy_type)

            if vendor in self.log_for_vendors:
                logger.info(
                    "Generated policy YAML:\n%s",
                yaml.dump(policy.YAMLConfig, sort_keys=False, default_flow_style=False),
                )
                logger.info(
                    "Generated services:\n%s",
                    yaml.dump(policy.services, sort_keys=False, default_flow_style=False),
                )

            assert policy.name == "Service_Group_Test_Policy"
            assert policy.YAMLConfig["filename"] == "Service_Group_Test_Policy"
            #assert policy.YAMLConfig["filters"][0]["header"]["targets"] == {vendor: f"Service_Group_Test_Policy {policy_type}"}
            assert len(policy.YAMLConfig["filters"][0]["terms"]) == len(sample_services)
            assert policy.YAMLConfig["filters"][0]["terms"][0]["name"] == "Test_Rule_for_Service_Group_1_Rule_0"
            assert policy.YAMLConfig["filters"][0]["terms"][1]["name"] == "Test_Rule_for_Service_Group_1_Rule_1"

            config = generate_config(policy)
            filepath = TEST_LOGPATH / "service_group" / f"{vendor.upper()}_generated_config.yaml"
            os.makedirs(TEST_LOGPATH / "service_group", exist_ok=True)
            for filename, content in config.items():
                if vendor in self.log_for_vendors:
                    logger.info(
                        "\n=== Generated config: %s ===\n%s\n=== End config ===",
                        filename,
                        content,
                    )
                with open(filepath, "w") as f:
                    f.write(
                        f"# Generated on {datetime.datetime.now()}\n# Test for generating using Service Group objects\n\n"
                    )
                    f.write(content)