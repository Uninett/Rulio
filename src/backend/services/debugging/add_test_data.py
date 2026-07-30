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

    device_specs = [
        ("edge-fw-01", "FortiGate", "Primary edge firewall for Trondheim office.", "firewall"),
        ("edge-fw-02", "FortiGate", "Secondary edge firewall for Trondheim office.", "firewall"),
        ("core-switch-01", "Cisco", "Core switch for Trondheim office.", "switch"),
        ("core-switch-02", "Cisco", "Secondary core switch for Trondheim office.", "switch"),
        ("edge-fw-03", "FortiGate", "Additional edge firewall for Oslo office.", "firewall"),
        ("edge-fw-04", "FortiGate", "Additional edge firewall for Oslo office.", "firewall"),
        ("core-switch-03", "Cisco", "Core switch for Oslo office.", "switch"),
        ("core-switch-04", "Cisco", "Secondary core switch for Oslo office.", "switch"),
        ("edge-fw-05", "Palo Alto", "Edge firewall for Copenhagen office.", "firewall"),
        ("edge-fw-06", "Palo Alto", "Edge firewall for Copenhagen office.", "firewall"),
        ("core-switch-05", "Arista", "Core switch for Copenhagen office.", "switch"),
        ("core-switch-06", "Arista", "Secondary core switch for Copenhagen office.", "switch"),
        ("edge-fw-07", "Check Point", "Edge firewall for Stockholm office.", "firewall"),
        ("edge-fw-08", "Check Point", "Edge firewall for Stockholm office.", "firewall"),
        ("core-switch-07", "Juniper", "Core switch for Stockholm office.", "switch"),
        ("core-switch-08", "Juniper", "Secondary core switch for Stockholm office.", "switch"),
        ("edge-fw-09", "Sophos", "Edge firewall for Helsinki office.", "firewall"),
        ("edge-fw-10", "Sophos", "Edge firewall for Helsinki office.", "firewall"),
        ("core-switch-09", "Huawei", "Core switch for Helsinki office.", "switch"),
        ("core-switch-10", "Huawei", "Secondary core switch for Helsinki office.", "switch"),
    ]

    created_devices = []
    for name, platform, description, device_type in device_specs:
        device_obj = get_or_create_device(
            actor=actor,
            tenant_id=tenant_id,
            name=name,
            platform=platform,
            description=description,
            type=device_type,
        )
        created_devices.append(device_obj)
        logger.info(f"Created {device_obj} for tenant={device_obj.tenant_id}")

    device, device2, device3, device4 = created_devices[:4]

    device_group_specs = [
        ("trondheim-firewalls", "Firewall devices in the Trondheim office."),
        ("trondheim-switches", "Switch devices in the Trondheim office."),
        ("oslo-firewalls", "Firewall devices in the Oslo office."),
        ("oslo-switches", "Switch devices in the Oslo office."),
        ("copenhagen-firewalls", "Firewall devices in the Copenhagen office."),
        ("copenhagen-switches", "Switch devices in the Copenhagen office."),
        ("stockholm-firewalls", "Firewall devices in the Stockholm office."),
        ("stockholm-switches", "Switch devices in the Stockholm office."),
        ("helsinki-firewalls", "Firewall devices in the Helsinki office."),
        ("helsinki-switches", "Switch devices in the Helsinki office."),
    ]

    created_device_groups = []
    for name, description in device_group_specs:
        device_group_obj = get_or_create_device_group(
            actor=actor,
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
        created_device_groups.append(device_group_obj)
        logger.info(f"Created {device_group_obj} for tenant={tenant_id}")

    device_group, device_group2 = created_device_groups[:2]

    for index, device_group_obj in enumerate(created_device_groups):
        device_ids = [device_obj.id for device_obj in created_devices[index * 2 : index * 2 + 2]]
        if len(device_ids) == 2:
            try:
                add_devices_to_group(
                    actor=actor,
                    tenant_id=tenant_id,
                    device_group_id=device_group_obj.id,
                    device_ids=device_ids,
                )
            except ValueError as e:
                logger.warning(str(e))

    interface, _, _, _, _, _ = get_or_create_interface(
        actor=actor,
        tenant_id=tenant_id,
        device_id=device.id,
        name="port1",
        description="External WAN interface.",
        type="physical",
    )
    logger.info(f"Created {interface} for device={device.id} and tenant={tenant_id}")

    interface2, _, _, _, _, _ = get_or_create_interface(
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
        direction="in",
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

    tag1, tag1_id, tag1_created = get_or_create_tag(
        actor=actor, tenant_id=tenant_id, name="web-servers", description="Tag for web servers."
    )

    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=device3)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=interface2)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=filter1)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag1, obj=address)

    tag2, tag2_id, tag2_created = get_or_create_tag(
        actor=actor, tenant_id=tenant_id, name="firewalls", description="Tag for firewall devices."
    )

    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device2)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device_group)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=device_group2)
    add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=tag2, obj=address)

    if default_tag := Tag.objects.filter(name="global", tenant_id=tenant_id).first():
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device2)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device3)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device_group)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=device_group2)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=interface)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=interface2)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=filter1)
        add_tag_to_object(actor=actor, tenant_id=tenant_id, tag=default_tag, obj=address)
