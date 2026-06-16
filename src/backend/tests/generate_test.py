
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



    @pytest.fixture
    def testing_addresses(self):
        testing_addresses = []
        testing_addresses.append(
            Address(
                name="Test_Address_1",
                description="This is a test address",
                tenant_id=42,
                ipv4_type="standard",
                ipv6_type=None,
                ipv4Network="192.168.1.0/24",
                ipv6Network=None,
                ipv4Address_start=None,
                ipv4Address_end=None,
                ipv6Address_start=None,
                ipv6Address_end=None,
            )
        )

        testing_addresses.append(
            Address(
                name="Test_Address_2",
            description="This is another test address",
            tenant_id=42,
            ipv4_type="standard",
            ipv6_type=None,
            ipv4Network="0.0.0.0/0",
            ipv6Network=None,
            ipv4Address_start=None,
            ipv4Address_end=None,
            ipv6Address_start=None,
            ipv6Address_end=None,
        )
        )
        return testing_addresses



    @pytest.fixture
    def address_policy_rule(self, testing_addresses):
        policy_rules = []
        for i, address in enumerate(testing_addresses):
            rule = PolicyRule(
                name=f"Test_Rule_{i+1}",
                obj_type="address",
                action="accept" if i % 2 == 0 else "deny",
                object = address,
                direction="destination" if i % 2 == 0 else "source",
            )
            policy_rules.append(rule)
        
        return policy_rules



    @pytest.fixture
    def testing_address_group(self, testing_addresses):
        address_group = AddressGroup(
            name="Test_Address_Group",
            description="This is a test address group",
            tenant_id=42,
        )

        # for address in testing_addresses:
        #     address_group.add_address_to_group(address)

        return address_group
    
    @pytest.fixture
    def address_group_policy_rule(self, testing_address_group):
        pass

    @pytest.fixture
    def testing_services(self):
        service1 = Service(
            name="Test_Service1",
            description="This is a test service",
            tenant_id=42,
            protocol="tcp",
            port_start=80,
            port_end=80,
        )

        service2 = Service(
            name="Test_Service2",
            description="This is another test service",
            tenant_id=42,
            protocol="udp",
            port_start=53,
            port_end=53,
        )


        return service1, service2
    
    @pytest.fixture
    def service_policy_rule(self, testing_services):
        service1, service2 = testing_services

        PolicyRule1 = PolicyRule(
            name="Test_Rule_1",
            obj_type="service",
            action="accept",
            object=service1,
            direction="destination",
        )

        PolicyRule2 = PolicyRule(
            name="Test_Rule_2",
            obj_type="service",
            action="deny",
            object=service2,
            direction="destination",
        )
        return [PolicyRule1, PolicyRule2]


    def test_generate_address_config(self, address_policy_rule):

        vendor = "cisco"
        policy_type = "extended"
        policy = Policy(
            name="Address_Test_Policy", rules=address_policy_rule, vendor=vendor, policy_type=policy_type
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
        assert policy.networks["networks"]["Test_Address_2"]["values"][0] == "0.0.0.0/0"
        assert policy.YAMLConfig["filters"][0]["terms"][1]["action"] == "deny"

        config = generate_config(policy)
        filepath = TEST_LOGPATH / "test_generate_address_config.yaml"
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

    def test_generate_address_group_config(self, testing_address_group):
        pass