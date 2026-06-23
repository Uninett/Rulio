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
            policy = Policy(
                name="Address_Test_Policy",
                rules=address_policy_rules,
                vendor=vendor,
                policy_type=policy_type,
            )

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

            terms = policy.YAMLConfig["filters"][0]["terms"]
            assert len(terms) == len({rule.sequence for rule in address_policy_rules})

            assert terms[0]["action"] == "accept"
            assert terms[0]["destination-address"] == ["Test_Address_1"]

            assert terms[1]["action"] == "deny"
            assert terms[1]["source-address"] == ["Test_Address_2"]

            assert policy.networks["networks"]["Test_Address_1"]["values"][0] == "192.168.1.0/24"

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

    def test_generate_address_group_config(self, address_group_policy_rules, request_with_session):
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(
                name="Address_Group_Test_Policy",
                rules=address_group_policy_rules,
                vendor=vendor,
                request=request_with_session,
                policy_type=policy_type,
            )

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

            terms = policy.YAMLConfig["filters"][0]["terms"]
            assert len(terms) == len({rule.sequence for rule in address_group_policy_rules})

            assert terms[0]["action"] == "accept"
            assert terms[0]["destination-address"] == ["Test_Address_Group_1"]

            assert terms[1]["action"] == "deny"
            assert terms[1]["source-address"] == ["Test_Address_Group_2"]

            assert "Test_Address_Group_1" in policy.networks["networks"]
            assert "Test_Address_Group_2" in policy.networks["networks"]

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

    def test_generate_service_config(self, service_policy_rules, request_with_session):
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(
                name="Service_Test_Policy",
                rules=service_policy_rules,
                vendor=vendor,
                request=request_with_session,
                policy_type=policy_type,
            )

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

            terms = policy.YAMLConfig["filters"][0]["terms"]
            assert len(terms) == len({rule.sequence for rule in service_policy_rules})

            assert terms[0]["protocol"] == "tcp"
            assert terms[0]["destination-port"] == ["Test_Service1"]

            assert terms[1]["protocol"] == "udp"
            assert terms[1]["destination-port"] == ["Test_Service2"]

            assert terms[2]["protocol"] == "tcp"
            assert terms[2]["destination-port"] == ["Test_Service3"]

            assert terms[3]["protocol"] == "udp"
            assert terms[3]["destination-port"] == ["Test_Service4"]

            assert terms[4]["protocol"] == "icmp"
            assert "destination-port" not in terms[4]

            assert terms[5]["protocol"] == "gre"
            assert "destination-port" not in terms[5]

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

    def test_generate_service_group_config(self, service_group_policy_rules, request_with_session):
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(
                name="Service_Group_Test_Policy",
                rules=service_group_policy_rules,
                vendor=vendor,
                request=request_with_session,
                policy_type=policy_type,
            )

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

            terms = policy.YAMLConfig["filters"][0]["terms"]

            expected_ports_by_protocol = {
                "tcp": ["Test_Service1", "Test_Service3"],
                "udp": ["Test_Service2", "Test_Service4"],
                "icmp": None,
                "gre": None,
            }

            assert len(terms) == len(expected_ports_by_protocol)

            seen_protocols = set()
            for term in terms:
                protocol = term["protocol"]
                seen_protocols.add(protocol)
                assert term["action"] == "accept"

                expected_ports = expected_ports_by_protocol[protocol]
                if expected_ports is None:
                    assert "destination-port" not in term
                else:
                    assert term["destination-port"] == expected_ports

            assert seen_protocols == set(expected_ports_by_protocol.keys())

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

    def test_generate_config_with_address_and_service(self, combined_policy_rules, request_with_session):
        for vendor, policy_type in self.vendor_policy_type_pairs:
            policy = Policy(
                name="Combined_Test_Policy",
                rules=combined_policy_rules,
                vendor=vendor,
                request=request_with_session,
                policy_type=policy_type,
            )

            if vendor in self.log_for_vendors:
                logger.info(
                    "Generated policy YAML:\n%s",
                    yaml.dump(policy.YAMLConfig, sort_keys=False, default_flow_style=False),
                )
                logger.info(
                    "Generated networks:\n%s",
                    yaml.dump(policy.networks, sort_keys=False, default_flow_style=False),
                )
                logger.info(
                    "Generated services:\n%s",
                    yaml.dump(policy.services, sort_keys=False, default_flow_style=False),
                )

            assert policy.name == "Combined_Test_Policy"
            assert policy.YAMLConfig["filename"] == "Combined_Test_Policy"

            terms = policy.YAMLConfig["filters"][0]["terms"]
            assert len(terms) == len({rule.sequence for rule in combined_policy_rules})

            assert terms[0]["action"] == "accept"
            assert terms[0]["protocol"] == "tcp"
            assert terms[0]["destination-address"] == ["Test_Address_1"]
            assert terms[0]["destination-port"] == ["Test_Service1"]

            assert terms[1]["action"] == "deny"
            assert terms[1]["protocol"] == "udp"
            assert terms[1]["source-address"] == ["Test_Address_2"]
            assert terms[1]["destination-port"] == ["Test_Service2"]

            config = generate_config(policy)
            filepath = TEST_LOGPATH / "combined" / f"{vendor.upper()}_generated_config.yaml"
            os.makedirs(TEST_LOGPATH / "combined", exist_ok=True)

            for filename, content in config.items():
                if vendor in self.log_for_vendors:
                    logger.info(
                        "\n=== Generated config: %s ===\n%s\n=== End config ===",
                        filename,
                        content,
                    )
                with open(filepath, "w") as f:
                    f.write(
                        f"# Generated on {datetime.datetime.now()}\n# Test for generating using both Address and Service objects\n\n"
                    )
                    f.write(content)