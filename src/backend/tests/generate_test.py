import copy
import pytest

from backend.services.config_generation.generate_config import (
    generate_config,
    generate_multi_policy_config,
    merge_policies,
)
from backend.utils.logger import clear_logs, set_up_logger
from backend.utils.write_to_file import write_configuration_to_file
from constants import TEST_LOGPATH


logger = set_up_logger(__name__)
clear_logs(__name__)


@pytest.mark.django_db
class TestGenerateConfig:
    vendor_target_spec_pairs = [
        ("juniper", None),
        ("arista", None),
        ("aruba", None),
        ("cisco", "mixed"),
        ("brocade", None),
        ("paloalto", ["from-zone", "internal", "to-zone", "external", "mixed"]),
    ]
    log_for_vendors = ["juniper"]

    def _extract_generated_text(self, config) -> str:
        assert config
        assert hasattr(config, "keys")
        assert len(config.keys()) >= 1

        generated_text = next(iter(config.values()))
        assert generated_text
        assert isinstance(generated_text, str)
        assert len(generated_text.strip()) > 0

        return generated_text

    def _generate_for_all_vendors(self, policy, output_subdir: str, output_prefix: str):
        generated_texts = {}

        for vendor, target_spec in self.vendor_target_spec_pairs:
            vendor_policy = copy.deepcopy(policy)
            vendor_policy.set_vendor(vendor, target_spec)

            config = generate_config(vendor_policy)
            generated_text = self._extract_generated_text(config)

            filepath = TEST_LOGPATH / output_subdir / f"{vendor.upper()}_{output_prefix}_generated_config.txt"
            filedir = TEST_LOGPATH / output_subdir
            write_configuration_to_file(
                config,
                filepath,
                filedir,
                vendor,
                __name__,
                generated_by=vendor,
                log_for_vendors=self.log_for_vendors,
            )

            generated_texts[vendor] = generated_text

        return generated_texts

    def test_generate_address_config(self, built_address_policy):
        configs = self._generate_for_all_vendors(
            policy=built_address_policy,
            output_subdir="addr",
            output_prefix="address",
        )

        for vendor, config in configs.items():
            if vendor == "paloalto":
                assert config
                continue

            assert "192.168.1.0" in config

        juniper_config = configs["juniper"]
        assert "Test_Address_Rule_1" in juniper_config
        assert "Test_Address_Rule_2" in juniper_config
        assert "192.168.1.0/24" in juniper_config

    def test_generate_address_group_config(self, built_address_group_policy):
        configs = self._generate_for_all_vendors(
            policy=built_address_group_policy,
            output_subdir="addr_group",
            output_prefix="address_group",
        )

        for vendor, config in configs.items():
            if vendor == "paloalto":
                assert config
                continue

            assert "10.0.0.0" in config
            assert "172.16.0.0" in config

        juniper_config = configs["juniper"]
        assert "Test_Rule_for_Address_Group_1" in juniper_config
        assert "Test_Rule_for_Address_Group_2" in juniper_config
        assert "10.0.0.0/8" in juniper_config

    def test_generate_service_config(self, built_service_policy):
        configs = self._generate_for_all_vendors(
            policy=built_service_policy,
            output_subdir="service",
            output_prefix="service",
        )

        for vendor, config in configs.items():
            if vendor == "paloalto":
                assert config
                continue

            assert "80" in config or "www" in config
            assert "53" in config or "domain" in config

        juniper_config = configs["juniper"]
        assert "Test_Service_Rule_1" in juniper_config
        assert "Test_Service_Rule_2" in juniper_config
        assert "destination-port 80;" in juniper_config
        assert "protocol tcp;" in juniper_config

    def test_generate_service_group_config(self, built_service_group_policy):
        configs = self._generate_for_all_vendors(
            policy=built_service_group_policy,
            output_subdir="service_group",
            output_prefix="service_group",
        )

        for vendor, config in configs.items():
            if vendor == "paloalto":
                assert config
                continue

            assert "80" in config or "www" in config
            assert "53" in config or "domain" in config

        juniper_config = configs["juniper"]
        assert "Test_Rule_for_Service_Group_1" in juniper_config
        assert "protocol tcp;" in juniper_config
        assert "protocol udp;" in juniper_config

    def test_generate_combined_config(self, built_combined_policy):
        configs = self._generate_for_all_vendors(
            policy=built_combined_policy,
            output_subdir="combined",
            output_prefix="combined",
        )

        for vendor, config in configs.items():
            if vendor == "paloalto":
                assert config
                continue

            assert "192.168.1.0" in config
            assert "80" in config or "www" in config
            assert "53" in config or "domain" in config

        juniper_config = configs["juniper"]
        assert "Combined_Rule_1" in juniper_config
        assert "Combined_Rule_2" in juniper_config
        assert "destination-port 80;" in juniper_config

    def test_generate_realistic_router_policy(self, built_realistic_acl_policy):
        configs = self._generate_for_all_vendors(
            policy=built_realistic_acl_policy,
            output_subdir="realistic",
            output_prefix="realistic",
        )

        for vendor, config in configs.items():
            if vendor == "paloalto":
                assert config
                continue

            assert "10.20.20.0" in config
            assert "172.16.20.53" in config
            assert "443" in config or "https" in config

        juniper_config = configs["juniper"]
        assert "Allow_Trusted_To_Web" in juniper_config
        assert "Allow_Trusted_To_DNS" in juniper_config
        assert "Deny_Admins_To_Blocked" in juniper_config
        assert "Allow_Admins_ICMP" in juniper_config
        assert "protocol icmp;" in juniper_config

    def test_generate_multi_policy_config(self, built_interface_policies):
        for vendor, target_spec in self.vendor_target_spec_pairs:
            vendor_policies = copy.deepcopy(built_interface_policies)

            for policy in vendor_policies:
                policy.set_vendor(vendor, target_spec)

            config = generate_multi_policy_config(vendor_policies)
            generated_text = self._extract_generated_text(config)

            filepath = TEST_LOGPATH / "multi" / f"{vendor.upper()}_multi_generated_config.txt"
            filedir = TEST_LOGPATH / "multi"
            write_configuration_to_file(
                config,
                filepath,
                filedir,
                vendor,
                __name__,
                generated_by=vendor,
                log_for_vendors=self.log_for_vendors,
            )

            assert generated_text

    def test_merge_policies_preserves_multiple_filters(self, built_interface_policies):
        merged_policy = merge_policies(copy.deepcopy(built_interface_policies))

        assert merged_policy is not None
        assert len(merged_policy.YAMLConfig["filters"]) == len(built_interface_policies)

        config = generate_config(merged_policy)
        generated_text = self._extract_generated_text(config)

        write_configuration_to_file(
            config,
            TEST_LOGPATH / "merged" / "MERGED_generated_config.txt",
            TEST_LOGPATH / "merged",
            merged_policy.vendor,
            __name__,
            generated_by="merged",
            log_for_vendors=self.log_for_vendors,
        )

        assert generated_text
