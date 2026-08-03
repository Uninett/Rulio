import pytest

from django.contrib.auth import get_user_model

from backend.services.attribute_objects.create_attribute_objects import create_service
from backend.services.config_generation.generate_interface_config import (
    InterfaceConfigGenerationResult,
    InterfaceDirectionGenerationResult,
    _build_direction_result,
    generate_interface_config_results,
    serialize_generated_config,
)
from backend.services.filter_objects.create_filter_objects import create_filter, create_rule
from backend.services.membership import add_filter_to_interface, add_objects_to_rule
from backend.services.tenant_objects.create_tenant_objects import create_device, create_interface


@pytest.mark.django_db
class TestGenerateInterfaceConfigHelpers:
    def test_interface_config_result_properties(self):
        result = InterfaceConfigGenerationResult(
            inbound=InterfaceDirectionGenerationResult(
                success=False,
                warnings=["in-warning"],
                errors=["in-error"],
            ),
            outbound=InterfaceDirectionGenerationResult(
                success=True,
                warnings=["out-warning"],
                errors=[],
            ),
        )

        assert result.has_errors is True
        assert result.has_warnings is True
        assert result.all_errors() == ["in-error"]
        assert result.all_warnings() == ["in-warning", "out-warning"]

    def test_serialize_generated_config(self):
        assert serialize_generated_config(None) == ""
        assert serialize_generated_config("abc") == "abc"

        class Dummy:
            def __str__(self):
                return "dummy-value"

        assert serialize_generated_config(Dummy()) == "dummy-value"


@pytest.mark.django_db
class TestGenerateInterfaceConfigResults:
    def _create_basic_interface(self, request_with_session, name="test-interface"):
        device = create_device(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name=f"{name}-device",
            platform="juniper",
            description="test device",
            type="firewall",
        )
        interface = create_interface(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name=name,
            description="test interface",
            device_id=device.id,
            type="layer3",
        )
        return device, interface

    def _create_filter_with_service_rule(
        self,
        request_with_session,
        filter_name,
        rule_name,
        service_name="test-service",
        rule_sequence=1,
        port=80,
    ):
        filter_obj = create_filter(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name=filter_name,
            description=f"{filter_name} description",
        )

        rule = create_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name=rule_name,
            filter=filter_obj,
            rule_sequence=rule_sequence,
            enable=True,
            description=f"{rule_name} description",
            action="accept",
            log_type="all",
            hit_count=0,
        )

        service = create_service(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            name=service_name,
            description=f"{service_name} description",
            protocol="tcp",
            port_start=port,
            port_end=port,
        )

        response = add_objects_to_rule(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            rule_id=rule.id,
            match_type="destination",
            objects=[service],
        )
        assert response["error_count"] == 0
        assert response["added_count"] == 1

        return filter_obj, rule, service

    def test_generate_interface_config_success_both_directions(self, request_with_session):
        _, interface = self._create_basic_interface(request_with_session, name="if-both")

        filter_in, _, _ = self._create_filter_with_service_rule(
            request_with_session,
            filter_name="Inbound_Filter",
            rule_name="Inbound_Rule",
            service_name="svc-in",
            port=80,
        )
        filter_out, _, _ = self._create_filter_with_service_rule(
            request_with_session,
            filter_name="Outbound_Filter",
            rule_name="Outbound_Rule",
            service_name="svc-out",
            port=443,
        )

        add_filter_to_interface(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
            filter_id=filter_in.id,
            direction="in",
            policy_sequence=10,
            enable=True,
        )
        add_filter_to_interface(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
            filter_id=filter_out.id,
            direction="out",
            policy_sequence=20,
            enable=True,
        )

        result = generate_interface_config_results(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
        )

        assert result.status == "success"
        assert result.has_errors is False
        assert result.has_warnings is False
        assert result.inbound.success is True
        assert result.outbound.success is True
        assert result.inbound.config is not None
        assert result.outbound.config is not None

    def test_generate_interface_config_success_with_warning_inbound_missing(self, request_with_session):
        _, interface = self._create_basic_interface(request_with_session, name="if-out-only")

        filter_out, _, _ = self._create_filter_with_service_rule(
            request_with_session,
            filter_name="Outbound_Only_Filter",
            rule_name="Outbound_Only_Rule",
            service_name="svc-out-only",
            port=443,
        )

        add_filter_to_interface(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
            filter_id=filter_out.id,
            direction="out",
            policy_sequence=20,
            enable=True,
        )

        result = generate_interface_config_results(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
        )

        assert result.status == "success_with_warnings"
        assert result.has_errors is False
        assert result.has_warnings is True
        assert result.inbound.success is False
        assert result.inbound.config is None
        assert result.inbound.errors == []
        assert result.inbound.warnings == [
            f"No filters found on interface_id={interface.id} tenant_id={request_with_session.tenant_id} for inbound direction"
        ]
        assert result.outbound.success is True
        assert result.outbound.config is not None
        assert result.outbound.errors == []

    def test_generate_interface_config_success_with_warning_outbound_missing(self, request_with_session):
        _, interface = self._create_basic_interface(request_with_session, name="if-in-only")

        filter_in, _, _ = self._create_filter_with_service_rule(
            request_with_session,
            filter_name="Inbound_Only_Filter",
            rule_name="Inbound_Only_Rule",
            service_name="svc-in-only",
            port=80,
        )

        add_filter_to_interface(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
            filter_id=filter_in.id,
            direction="in",
            policy_sequence=10,
            enable=True,
        )

        result = generate_interface_config_results(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
        )

        assert result.status == "success_with_warnings"
        assert result.has_errors is False
        assert result.has_warnings is True
        assert result.inbound.success is True
        assert result.inbound.config is not None
        assert result.inbound.errors == []
        assert result.outbound.success is False
        assert result.outbound.config is None
        assert result.outbound.errors == []
        assert result.outbound.warnings == [
            f"No filters found on interface_id={interface.id} tenant_id={request_with_session.tenant_id} for outbound direction"
        ]

    def test_generate_interface_config_error_when_no_filters_on_either_direction(self, request_with_session):
        _, interface = self._create_basic_interface(request_with_session, name="if-no-filters")

        result = generate_interface_config_results(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
        )

        expected_error = (
            f"No filters found on interface_id={interface.id} tenant_id={request_with_session.tenant_id} for either direction"
        )

        assert result.status == "error"
        assert result.has_errors is True
        assert result.inbound.errors == [expected_error]
        assert result.outbound.errors == [expected_error]

    def test_generate_interface_config_error_for_wrong_tenant_non_superuser(
        self,
        request_with_session,
        create_testing_tenant,
    ):
        User = get_user_model()
        normal_user = User.objects.create_user(username="normal-user", password="change-me")

        _, interface = self._create_basic_interface(request_with_session, name="if-tenant-check")

        other_tenant = create_testing_tenant.id + 999

        result = generate_interface_config_results(
            actor=normal_user,
            tenant_id=other_tenant,
            interface_id=interface.id,
        )

        expected_error = (
            f"Interface with id={interface.id} belongs to tenant_id={request_with_session.tenant_id}, "
            f"but request was made for tenant_id={other_tenant}"
        )

        assert result.status == "error"
        assert result.has_errors is True
        assert result.inbound.errors == [expected_error]
        assert result.outbound.errors == [expected_error]

    def test_generate_interface_config_allows_superuser_cross_tenant(self, create_testing_tenant):
        User = get_user_model()
        superuser = User.objects.create_superuser(username="root", password="change-me")

        device = create_device(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            name="superuser-device",
            platform="juniper",
            description="superuser device",
            type="firewall",
        )
        interface = create_interface(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            name="superuser-interface",
            description="superuser interface",
            device_id=device.id,
            type="layer3",
        )

        filter_obj = create_filter(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            name="Superuser_Filter",
            description="superuser filter",
        )
        rule = create_rule(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            name="Superuser_Rule",
            filter=filter_obj,
            rule_sequence=1,
            enable=True,
            description="superuser rule",
            action="accept",
            log_type="all",
            hit_count=0,
        )
        service = create_service(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            name="superuser-service",
            description="superuser service",
            protocol="tcp",
            port_start=443,
            port_end=443,
        )
        response = add_objects_to_rule(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            rule_id=rule.id,
            match_type="destination",
            objects=[service],
        )
        assert response["error_count"] == 0
        assert response["added_count"] == 1

        add_filter_to_interface(
            actor=superuser,
            tenant_id=create_testing_tenant.id,
            interface_id=interface.id,
            filter_id=filter_obj.id,
            direction="in",
            policy_sequence=10,
            enable=True,
        )

        requested_tenant_id = create_testing_tenant.id + 123

        result = generate_interface_config_results(
            actor=superuser,
            tenant_id=requested_tenant_id,
            interface_id=interface.id,
        )

        assert result.status == "success_with_warnings"
        assert result.inbound.success is True
        assert result.outbound.success is False
        assert result.outbound.warnings == [
            f"No filters found on interface_id={interface.id} tenant_id={requested_tenant_id} for outbound direction"
        ]

    def test_build_direction_result_returns_error_for_invalid_direction(self, request_with_session):
        _, interface = self._create_basic_interface(request_with_session, name="if-invalid-direction")

        result = _build_direction_result(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            interface_id=interface.id,
            direction="invalid",
        )

        assert result.success is False
        assert result.config is None
        assert result.warnings == []
        assert len(result.errors) == 1
        assert "Failed to generate invalid config" in result.errors[0]