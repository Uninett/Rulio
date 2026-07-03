from django.contrib.auth.models import User

from backend.objects.attributes.tag import Tag
from backend.services.attribute_objects.create_attribute_objects import get_or_create_address, get_or_create_tag
from backend.services.filter_objects.create_filter_objects import get_or_create_filter
from backend.services.tenant_objects.create_tenant_objects import get_or_create_device
from backend.services.helper_user_tenant import require_write_tenant
from backend.services.membership import add_devices_to_group, add_filter_to_interface, add_tag_to_object
from backend.services.tenant_objects.create_tenant_objects import (
    get_or_create_device_group,
    get_or_create_interface,
)
from backend.utils.logger import set_up_logger


logger = set_up_logger(__name__)


def create_interfaces_devices_devicegroups_tags(*, actor: User, tenant_id: int):
    require_write_tenant(actor, tenant_id)

    device = get_or_create_device(
        actor=actor,
        tenant_id=tenant_id,
        name="edge-fw-01",
        platform="FortiGate",
        description="Primary edge firewall for Trondheim office.",
        type="firewall",
    )
    logger.info(f"Created {device} for tenant={device.tenant_id}")

    device2 = get_or_create_device(
        actor=actor,
        tenant_id=tenant_id,
        name="edge-fw-02",
        platform="FortiGate",
        description="Secondary edge firewall for Trondheim office.",
        type="firewall",
    )
    logger.info(f"Created {device2} for tenant={device2.tenant_id}")

    device3 = get_or_create_device(
        actor=actor,
        tenant_id=tenant_id,
        name="core-switch-01",
        platform="Cisco",
        description="Core switch for Trondheim office.",
        type="switch",
    )
    logger.info(f"Created {device3} for tenant={device3.tenant_id}")

    device_group = get_or_create_device_group(
        actor=actor,
        tenant_id=tenant_id,
        name="trondheim-firewalls",
        description="Firewall devices in the Trondheim office.",
    )
    logger.info(f"Created {device_group} for tenant={tenant_id}")

    device_group2 = get_or_create_device_group(
        actor=actor,
        tenant_id=tenant_id,
        name="trondheim-switches",
        description="Switch devices in the Trondheim office.",
    )
    logger.info(f"Created {device_group2} for tenant={tenant_id}")

    try:
        add_devices_to_group(
            actor=actor, tenant_id=tenant_id, device_group_id=device_group.id, device_ids=[device.id, device2.id]
        )
    except ValueError as e:
        logger.warning(str(e))

    interface, _ = get_or_create_interface(
        actor=actor,
        tenant_id=tenant_id,
        device_id=device.id,
        name="port1",
        description="External WAN interface.",
        type="physical",
    )
    logger.info(f"Created {interface} for device={device.id} and tenant={tenant_id}")

    interface2, _ = get_or_create_interface(
        actor=actor,
        tenant_id=tenant_id,
        device_id=device3.id,
        name="port2",
        description="Internal LAN interface.",
        type="physical",
    )
    logger.info(f"Created {interface2} for device={device3.id} and tenant={tenant_id}")

    filter1, _ = get_or_create_filter(
        actor=actor,
        tenant_id=tenant_id,
        name="Allow HTTP",
        description="Allow HTTP traffic.",
    )
    logger.info(f"Created {filter1} for tenant={tenant_id}")

    add_filter_to_interface(
        actor=actor,
        tenant_id=tenant_id,
        interface_id=interface2.id,
        filter_id=filter1.id,
        policy_sequence=1,
        enable=True,
    )

    address, _, _ = get_or_create_address(
        actor=actor,
        tenant_id=tenant_id,
        name="web-server-01",
        description="Web server in Trondheim office.",
        addr_type="host",
        ipv4_type="standard",
        ipv4Network="192.168.1.0/24",
    )

    tag1, tag1_created = get_or_create_tag(
        actor=actor, tenant_id=tenant_id, name="web-servers", description="Tag for web servers."
    )

    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=device3)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=interface2)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=filter1)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=address)

    tag2, tag2_created = get_or_create_tag(
        actor=actor, tenant_id=tenant_id, name="firewalls", description="Tag for firewall devices."
    )

    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device2)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device_group)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device_group2)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=address)

    if default_tag := Tag.objects.filter(name="default", tenant_id=tenant_id).first():
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device2)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device3)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device_group)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device_group2)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=interface)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=interface2)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=filter1)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=address)
