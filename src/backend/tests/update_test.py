import ipaddress
import pytest

from backend.services.update import (
    update_address,
    update_service,
    update_address_group,
    update_service_group,
    update_rule,
    update_filter,
    update_device,
    update_device_group,
    update_interface,
    update_tag,
)


def convert_ipv4_to_ipv6(ipv4_network):
    if ipv4_network is None:
        return None

    value = str(ipv4_network).strip()

    if "/" in value:
        net = ipaddress.IPv4Network(value, strict=False)
        ipv6_addr = ipaddress.IPv6Address(f"::ffff:{net.network_address}")
        return ipaddress.IPv6Network((ipv6_addr, 96 + net.prefixlen), strict=False)

    addr = ipaddress.IPv4Address(value)
    ipv6_addr = ipaddress.IPv6Address(f"::ffff:{addr}")
    return ipaddress.IPv6Network((ipv6_addr, 128), strict=False)


@pytest.mark.django_db
class TestUpdate:
    def test_update_address(self, request_with_session, sample_addresses):
        for address in sample_addresses:
            new_name = f"{address.name}_updated"

            update_address(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                address_id=address.id,
                name=new_name,
                description="updated address description",
            )

            address.refresh_from_db()
            assert address.name == new_name
            assert address.description == "updated address description"

            if address.ipv4_type == "standard" and not address.ipv6_type and address.ipv4Network:
                old_ipv4_network = address.ipv4Network

                update_address(
                    actor=request_with_session.user,
                    tenant_id=request_with_session.tenant_id,
                    address_id=address.id,
                    ipv6_type="standard",
                    ipv6Network=convert_ipv4_to_ipv6(old_ipv4_network),
                )

                address.refresh_from_db()
                assert address.ipv6_type == "standard"
                assert str(address.ipv6Network) == str(convert_ipv4_to_ipv6(old_ipv4_network))

    def test_update_service(self, request_with_session, sample_services):
        for service in sample_services:
            new_name = f"{service.name}_updated"

            update_service(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                service_id=service.id,
                name=new_name,
                description="updated service description",
                port_start=1000,
                port_end=2000,
            )

            service.refresh_from_db()
            assert service.name == new_name
            assert service.description == "updated service description"
            assert service.port_start == 1000
            assert service.port_end == 2000

    def test_update_address_group(self, request_with_session, sample_address_group):
        for address_group in sample_address_group:
            new_name = f"{address_group.name}_updated"

            update_address_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                address_group_id=address_group.id,
                name=new_name,
                description="updated address group description",
            )

            address_group.refresh_from_db()
            assert address_group.name == new_name
            assert address_group.description == "updated address group description"

    def test_update_address_group_invalid_type(self, request_with_session, sample_address_group):
        address_group = sample_address_group[0]
        old_name = address_group.name

        with pytest.raises(ValueError, match="Address group type must be 'group'"):
            update_address_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                address_group_id=address_group.id,
                addr_type="standard",
            )

        address_group.refresh_from_db()
        assert address_group.name == old_name

    def test_update_service_group(self, request_with_session, sample_service_group):
        service_group = sample_service_group
        new_name = f"{service_group.name}_updated"

        update_service_group(
            actor=request_with_session.user,
            tenant_id=request_with_session.tenant_id,
            service_group_id=service_group.id,
            name=new_name,
            description="updated service group description",
        )

        service_group.refresh_from_db()
        assert service_group.name == new_name
        assert service_group.description == "updated service group description"

    def test_update_service_group_invalid_type(self, request_with_session, sample_service_group):
        service_group = sample_service_group

        with pytest.raises(ValueError, match="Service group type must be 'group'"):
            update_service_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                service_group_id=service_group.id,
                service_type="tcp",
            )

    def test_update_device(self, request_with_session, sample_devices):
        for device in sample_devices:
            new_name = f"{device.name}_updated"

            update_device(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                device_id=device.id,
                name=new_name,
                description="updated device description",
                platform="updated-platform",
                type="updated-type",
            )

            device.refresh_from_db()
            assert device.name == new_name
            assert device.description == "updated device description"
            assert device.platform == "updated-platform"
            assert device.type == "updated-type"

    def test_update_device_group(self, request_with_session, sample_device_groups):
        for device_group in sample_device_groups:
            new_name = f"{device_group.name}_updated"

            update_device_group(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                device_group_id=device_group.id,
                name=new_name,
                description="updated device group description",
            )

            device_group.refresh_from_db()
            assert device_group.name == new_name
            assert device_group.description == "updated device group description"

    def test_update_tag(self, request_with_session, sample_tags):
        for tag in sample_tags:
            new_name = f"{tag.name}_updated"

            update_tag(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                tag_id=tag.id,
                name=new_name,
                description="updated tag description",
            )

            tag.refresh_from_db()
            assert tag.name == new_name
            assert tag.description == "updated tag description"

    def test_update_interface(self, request_with_session, sample_interfaces):
        for interface in sample_interfaces:
            new_name = f"{interface.name}_updated"

            update_interface(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                interface_id=interface.id,
                name=new_name,
                description="updated interface description",
                type="layer3",
                VRF="updated-vrf",
            )

            interface.refresh_from_db()
            assert interface.name == new_name
            assert interface.description == "updated interface description"
            assert interface.type == "layer3"
            assert interface.VRF == "updated-vrf"

    def test_update_filter(self, request_with_session, sample_filters):
        for filter_obj in sample_filters:
            new_name = f"{filter_obj.name}_updated"

            update_filter(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                filter_id=filter_obj.id,
                name=new_name,
                description="updated filter description",
            )

            filter_obj.refresh_from_db()
            assert filter_obj.name == new_name
            assert filter_obj.description == "updated filter description"

    def test_update_rule(self, request_with_session, sample_rules):
        for rule in sample_rules:
            new_name = f"{rule.name}_updated"

            update_rule(
                actor=request_with_session.user,
                tenant_id=request_with_session.tenant_id,
                rule_id=rule.id,
                name=new_name,
                description="updated rule description",
                action="deny",
                log_type="start",
                hit_count=123,
                rule_sequence=rule.rule_sequence,
            )

            rule.refresh_from_db()
            assert rule.name == new_name
            assert rule.description == "updated rule description"
            assert rule.action == "deny"
            assert rule.log_type == "start"
            assert rule.hit_count == 123
            assert rule.rule_sequence == rule.rule_sequence
