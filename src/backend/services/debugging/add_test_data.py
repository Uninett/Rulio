from django.contrib.auth.models import User

from backend.objects.attributes.tag import Tag
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
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


def create_interfaces_devices_devicegroups_tags(*, actor: User, tenant_id: int, tenants: list):
    require_write_tenant(actor, tenant_id)

    current_tenant = next((tenant for tenant in tenants if getattr(tenant, "id", None) == tenant_id), None)

    target_tenants = [tenant for tenant in tenants if getattr(tenant, "tenant_name", "").lower() in {"ntnu", "sikt"}]
    if not target_tenants and current_tenant is not None:
        target_tenants = [current_tenant]

    if not target_tenants:
        logger.warning("No relevant tenants were provided for test data seeding.")
        return

    for target_tenant in target_tenants:
        target_tenant_name = getattr(target_tenant, "tenant_name", "") or ""
        normalized_tenant_name = target_tenant_name.lower()
        is_ntnu_or_sikt_tenant = any(marker in normalized_tenant_name for marker in ["ntnu", "sikt"])

        tenant_prefix = (
            "ntnu" if "ntnu" in normalized_tenant_name else "sikt" if "sikt" in normalized_tenant_name else "shared"
        )
        tenant_label = f"{tenant_prefix.upper()}" if tenant_prefix != "shared" else "SHARED"

        device_specs = [
            (
                f"{tenant_prefix}-edge-fw-01",
                "Juniper",
                f"Primary edge firewall for {tenant_label} office.",
                "firewall",
            ),
            (
                f"{tenant_prefix}-edge-fw-02",
                "Juniper",
                f"Secondary edge firewall for {tenant_label} office.",
                "firewall",
            ),
            (f"{tenant_prefix}-core-sw-01", "Cisco", f"Core switch for {tenant_label} office.", "switch"),
            (f"{tenant_prefix}-core-sw-02", "Cisco", f"Secondary core switch for {tenant_label} office.", "switch"),
            (f"{tenant_prefix}-router-01", "Cisco", f"Primary router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-02", "Juniper", f"Secondary router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-03", "Brocade", f"Edge router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-04", "Cisco", f"Backup router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-05", "Juniper", f"Distribution router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-06", "Brocade", f"Aggregation router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-07", "Cisco", f"WAN router for {tenant_label} office.", "router"),
            (f"{tenant_prefix}-router-08", "Juniper", f"LAN router for {tenant_label} office.", "router"),
        ]

        if is_ntnu_or_sikt_tenant:
            device_specs.extend(
                [
                    (
                        f"{tenant_prefix}-edge-fw-03",
                        "Juniper",
                        f"Additional edge firewall for {tenant_label} testing.",
                        "firewall",
                    ),
                    (
                        f"{tenant_prefix}-edge-fw-04",
                        "Juniper",
                        f"Additional edge firewall for {tenant_label} testing.",
                        "firewall",
                    ),
                    (
                        f"{tenant_prefix}-core-sw-03",
                        "Cisco",
                        f"Additional core switch for {tenant_label} testing.",
                        "switch",
                    ),
                    (
                        f"{tenant_prefix}-core-sw-04",
                        "Cisco",
                        f"Additional core switch for {tenant_label} testing.",
                        "switch",
                    ),
                    (f"{tenant_prefix}-router-09", "Brocade", f"Campus router for {tenant_label} testing.", "router"),
                    (f"{tenant_prefix}-router-10", "Juniper", f"Campus router for {tenant_label} testing.", "router"),
                ]
            )

        created_devices = []
        for name, platform, description, device_type in device_specs:
            device_obj = get_or_create_device(
                actor=actor,
                tenant_id=target_tenant.id,
                name=name,
                platform=platform,
                description=description,
                type=device_type,
            )
            created_devices.append(device_obj)
            logger.info(f"Created {device_obj} for tenant={device_obj.tenant_id}")

        device, device2, device3, device4 = created_devices[:4]

        created_interfaces = []
        for index, device_obj in enumerate(created_devices):
            interface_obj, _, _, _, _, _ = get_or_create_interface(
                actor=actor,
                tenant_id=target_tenant.id,
                device_id=device_obj.id,
                name=f"port{index + 1}",
                description=f"Interface {index + 1} for {device_obj.name}.",
                type="physical",
            )
            created_interfaces.append(interface_obj)
            logger.info(f"Created {interface_obj} for device={device_obj.id} and tenant={target_tenant.id}")

        device_group_specs = [
            (f"{tenant_prefix}-firewalls", f"Firewall devices for {tenant_label} office."),
            (f"{tenant_prefix}-switches", f"Switch devices for {tenant_label} office."),
            (f"{tenant_prefix}-routers", f"Router devices for {tenant_label} office."),
        ]

        if is_ntnu_or_sikt_tenant:
            device_group_specs.extend(
                [
                    (
                        f"{tenant_prefix}-campus-firewalls",
                        f"Additional firewall group for {tenant_label} campus testing.",
                    ),
                    (
                        f"{tenant_prefix}-security-switches",
                        f"Additional switch group for {tenant_label} security testing.",
                    ),
                    (f"{tenant_prefix}-shared-services", f"Shared services group for {tenant_label} testing."),
                ]
            )

        created_device_groups = []
        for name, description in device_group_specs:
            device_group_obj = get_or_create_device_group(
                actor=actor,
                tenant_id=target_tenant.id,
                name=name,
                description=description,
            )
            created_device_groups.append(device_group_obj)
            logger.info(f"Created {device_group_obj} for tenant={target_tenant.id}")

        device_group, device_group2 = created_device_groups[:2]

        for index, device_group_obj in enumerate(created_device_groups):
            device_ids = [device_obj.id for device_obj in created_devices[index * 2 : index * 2 + 2]]
            if len(device_ids) == 2:
                try:
                    add_devices_to_group(
                        actor=actor,
                        tenant_id=target_tenant.id,
                        device_group_id=device_group_obj.id,
                        device_ids=device_ids,
                    )
                except ValueError as e:
                    logger.warning(str(e))

        interface = created_interfaces[0] if created_interfaces else None
        interface2 = (
            created_interfaces[2]
            if len(created_interfaces) > 2
            else created_interfaces[0]
            if created_interfaces
            else None
        )

        if interface is None or interface2 is None:
            interface = get_or_create_interface(
                actor=actor,
                tenant_id=target_tenant.id,
                device_id=device.id,
                name="port1",
                description="External WAN interface.",
                type="physical",
            )[0]
            interface2 = get_or_create_interface(
                actor=actor,
                tenant_id=target_tenant.id,
                device_id=device3.id,
                name="port2",
                description="Internal LAN interface.",
                type="physical",
            )[0]
        logger.info(f"Created {interface} for device={device.id} and tenant={target_tenant.id}")
        logger.info(f"Created {interface2} for device={device3.id} and tenant={target_tenant.id}")

        filter1, _ = get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name="Allow HTTP",
            description="Allow HTTP traffic.",
        )
        logger.info(f"Created {filter1} for tenant={target_tenant.id}")

        add_filter_to_interface(
            actor=actor,
            tenant_id=target_tenant.id,
            interface_id=interface2.id,
            filter_id=filter1.id,
            policy_sequence=1,
            enable=True,
            direction="in",
        )

        address, _, _ = get_or_create_address(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-web-server-01",
            description="Web server in Trondheim office.",
            addr_type="host",
            ipv4_type="standard",
            ipv4Network="192.168.1.0/24",
        )

        tag1, tag1_id, tag1_created = get_or_create_tag(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-web-servers",
            description="Tag for web servers.",
        )

        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag1, obj=device3)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag1, obj=interface2)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag1, obj=filter1)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag1, obj=address)

        tag2, tag2_id, tag2_created = get_or_create_tag(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-firewalls",
            description="Tag for firewall devices.",
        )

        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag2, obj=device)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag2, obj=device2)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag2, obj=device_group)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag2, obj=device_group2)
        add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=tag2, obj=address)

        if default_tag := Tag.objects.filter(name="global", tenant_id=target_tenant.id).first():
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=device)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=device2)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=device3)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=device_group)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=device_group2)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=interface)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=interface2)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=filter1)
            add_tag_to_object(actor=actor, tenant_id=target_tenant.id, tag=default_tag, obj=address)

        tenant_admin, created_admin = User.objects.get_or_create(
            username=f"{tenant_prefix.upper()}TenantAdmin",
            defaults={"email": f"tenantadmin@{tenant_prefix}.no"},
        )
        if created_admin:
            tenant_admin.set_password("change-me")
            tenant_admin.save(update_fields=["password"])
        TenantUserMember.objects.get_or_create(
            tenant=target_tenant,
            user_id=int(tenant_admin.id),
            defaults={"role": TenantUserMember.TenantRole.ADMIN},
        )

        tenant_member, created_member = User.objects.get_or_create(
            username=f"{tenant_prefix.upper()}TenantMember",
            defaults={"email": f"tenantmember@{tenant_prefix}.no"},
        )
        if created_member:
            tenant_member.set_password("change-me")
            tenant_member.save(update_fields=["password"])
        TenantUserMember.objects.get_or_create(
            tenant=target_tenant,
            user_id=int(tenant_member.id),
            defaults={"role": TenantUserMember.TenantRole.MEMBER},
        )

        if normalized_tenant_name == "ntnu":
            cross_tenant_user, created_cross_tenant_user = User.objects.get_or_create(
                username="NTNU_Admin_Sikt_Member",
                defaults={"email": "ntnuadmin@sikt.no"},
            )
            if created_cross_tenant_user:
                cross_tenant_user.set_password("change-me")
                cross_tenant_user.save(update_fields=["password"])
            TenantUserMember.objects.get_or_create(
                tenant=target_tenant,
                user_id=int(cross_tenant_user.id),
                defaults={"role": TenantUserMember.TenantRole.ADMIN},
            )

        if normalized_tenant_name == "sikt":
            cross_tenant_user, created_cross_tenant_user = User.objects.get_or_create(
                username="NTNU_Admin_Sikt_Member",
                defaults={"email": "ntnuadmin@sikt.no"},
            )
            if created_cross_tenant_user:
                cross_tenant_user.set_password("change-me")
                cross_tenant_user.save(update_fields=["password"])
            TenantUserMember.objects.get_or_create(
                tenant=target_tenant,
                user_id=int(cross_tenant_user.id),
                defaults={"role": TenantUserMember.TenantRole.MEMBER},
            )
