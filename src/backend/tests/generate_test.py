
import datetime
import os
import yaml
import pytest

from backend.services.generate_config import generate_config, PolicyRule, Policy
from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup
#from backend.services.membership import add_address_to_group, add_service_to_group
from backend.utils.logger import set_up_logger
from constants import TEST_LOGPATH


logger = set_up_logger(__name__)


class TestGenerateConfig:






    def test_generate_address_config(self, address_policy_rules):
        
        vendor = "juniper"
        policy_type = ""
        policy = Policy(
            name="Address_Test_Policy", rules=address_policy_rules, vendor=vendor, policy_type=policy_type
        )

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
        assert policy.YAMLConfig["filters"][0]["header"]["targets"] == {
            vendor: f"Address_Test_Policy {policy_type}"
        }
        assert len(policy.YAMLConfig["filters"][0]["terms"]) == 2
        assert policy.YAMLConfig["filters"][0]["terms"][0]["name"] == "Test_Rule_1"
        assert (
            policy.YAMLConfig["filters"][0]["terms"][0]["destination-address"]
            == "Test_Address_1"
        )
        assert policy.networks["networks"]["Test_Address_1"]["values"][0] == "192.168.1.0/24"
        assert policy.YAMLConfig["filters"][0]["terms"][0]["action"] == "accept"
        assert policy.YAMLConfig["filters"][0]["terms"][1]["name"] == "Test_Rule_2"
        assert (
            policy.YAMLConfig["filters"][0]["terms"][1]["source-address"]
            == "Test_Address_2"
        )
        #assert policy.networks["networks"]["Test_Address_2"]["values"][0] == "0.0.0.0/0"
        assert policy.YAMLConfig["filters"][0]["terms"][1]["action"] == "deny"

        config = generate_config(policy)
        filepath = TEST_LOGPATH / f"test_generate_address_config_for_{vendor}.yaml"
        os.makedirs(TEST_LOGPATH, exist_ok=True)
        
        for filename, content in config.items():
            logger.info(
                "\n=== Generated config: %s ===\n%s\n=== End config ===",
                filename,
                content,
            )
            with open(filepath, "w") as f:
                f.write(f"# Generated on {datetime.datetime.now()}\n# Test for generating using only Address objects\n\n")
                f.write(content)

    def test_generate_address_group_config(self, address_group_policy_rules):
        pass