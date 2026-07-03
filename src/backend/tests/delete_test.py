import pytest

from backend.objects.attributes.tag import Tag
from backend.objects.filters.filter import Filter
from backend.objects.filters.rule import Rule
from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.interface import Interface
from backend.services.delete import (
    delete_tag_from_tenant,
    delete_rule,
    delete_device,
    delete_interface,
    delete_filter,
)


@pytest.mark.django_db
class TestDelete:
    def test_delete_tag_from_tenant(self, request_with_session, sample_tags):
        for tag in sample_tags:
            tag_id = tag.id
            assert Tag.objects.filter(id=tag_id).exists()

            deleted_count = delete_tag_from_tenant(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                tag_id=tag_id,
            )

            assert deleted_count >= 1
            assert Tag.objects.filter(id=tag_id).exists() is False

    def test_delete_rule(self, request_with_session, sample_rules):
        for rule in sample_rules:
            rule_id = rule.id
            assert Rule.objects.filter(id=rule_id).exists()

            delete_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rule_id,
            )

            assert Rule.objects.filter(id=rule_id).exists() is False

    def test_delete_device(self, request_with_session, sample_devices):
        for device in sample_devices:
            device_id = device.id
            assert Device.objects.filter(id=device_id).exists()

            result = delete_device(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                device_id=device_id,
            )

            assert result == {"status": "success", "device": {"id": device_id}}
            assert Device.objects.filter(id=device_id).exists() is False

    def test_delete_interface(self, request_with_session, sample_interfaces):
        for interface in sample_interfaces:
            interface_id = interface.id
            assert Interface.objects.filter(id=interface_id).exists()

            result = delete_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=interface_id,
            )

            assert result == {"status": "success", "interface": {"id": interface_id}}
            assert Interface.objects.filter(id=interface_id).exists() is False

    def test_delete_filter(self, request_with_session, sample_filters):
        for filter_obj in sample_filters:
            filter_id = filter_obj.id
            assert Filter.objects.filter(id=filter_id).exists()

            result = delete_filter(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                filter_id=filter_id,
            )

            assert result == {"status": "success", "filter": {"id": filter_id}}
            assert Filter.objects.filter(id=filter_id).exists() is False

    def test_delete_rule_invalid_id(self, request_with_session):
        with pytest.raises(ValueError, match=r"Rule with id=999999 does not exist"):
            delete_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=999999,
            )

    def test_delete_device_invalid_id(self, request_with_session):
        with pytest.raises(ValueError, match=r"Device with id=999999 does not exist"):
            delete_device(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                device_id=999999,
            )

    def test_delete_interface_invalid_id(self, request_with_session):
        with pytest.raises(ValueError, match=r"Interface with id=999999 does not exist"):
            delete_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=999999,
            )

    def test_delete_filter_invalid_id(self, request_with_session):
        with pytest.raises(ValueError, match=r"Filter with id=999999 does not exist"):
            delete_filter(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                filter_id=999999,
            )

    def test_delete_tag_from_tenant_invalid_id(self, request_with_session):
        with pytest.raises(ValueError, match=r"Tag with id=999999 does not exist"):
            delete_tag_from_tenant(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                tag_id=999999,
            )
