from django.contrib.auth.models import User

from backend.objects.attributes.tag import Tag
from backend.objects.tenant_objects.tenant_user_member import TenantUserMember
from backend.services.attribute_objects.create_attribute_objects import get_or_create_address, get_or_create_service, get_or_create_tag
from backend.services.filter_objects.create_filter_objects import get_or_create_filter, get_or_create_rule
from backend.services.tenant_objects.create_tenant_objects import get_or_create_device
from backend.services.helper_user_tenant import require_write_tenant
from backend.services.membership import add_devices_to_group, add_filter_to_interface, add_objects_to_rule, add_tag_to_object
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
      

        f1=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-http",
            description=f"Allow HTTP traffic for {tenant_label} office.",
        )[0]

        r1 = get_or_create_rule(
            actor=actor,
            filter=f1,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-http-rule",
            description=f"Allow HTTP traffic for {tenant_label} office.",
            action="accept",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        s1 = get_or_create_service(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-http-service",
            description=f"HTTP service for {tenant_label} office.",
            protocol="tcp",
            port_start=80,
            port_end=80,
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r1.id, match_type="any", objects=[s1])
        
        f2=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-https",
            description=f"Allow HTTPS traffic for {tenant_label} office.",
        )[0]
        r2 = get_or_create_rule(
            actor=actor,
            filter=f2,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-https-rule",
            description=f"Allow HTTPS traffic for {tenant_label} office.",
            action="accept",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        s2 = get_or_create_service(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-https-service",
            description=f"HTTPS service for {tenant_label} office.",
            protocol="tcp",
            port_start=443,
            port_end=443,
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r2.id, match_type="any", objects=[s2])

        f3=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-ssh",
            description=f"Allow SSH traffic for {tenant_label} office.",
        )[0]
        r3 = get_or_create_rule(
            actor=actor,
            filter=f3,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-ssh-rule",
            description=f"Allow SSH traffic for {tenant_label} office.",
            action="accept",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        s3 = get_or_create_service(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-ssh-service",
            description=f"SSH service for {tenant_label} office.",
            protocol="tcp",
            port_start=22,
            port_end=22,
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r3.id, match_type="any", objects=[s3])

        f4=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-deny-external",
            description=f"Deny external traffic for {tenant_label} office.",
        )[0]
        r4 = get_or_create_rule(
            actor=actor,
            filter=f4,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-deny-external-rule",
            description=f"Deny external traffic for {tenant_label} office.",
            action="deny",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        a1 = get_or_create_address(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-external-network",
            description=f"External network for {tenant_label} office.",
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="10.0.0.0/8",
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r4.id, match_type="source", objects=[a1])

        f5=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-dns",
            description=f"Allow DNS traffic for {tenant_label} office.",
        )[0]
        r5 = get_or_create_rule(
            actor=actor,
            filter=f5,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-dns-rule",
            description=f"Allow DNS traffic for {tenant_label} office.",
            action="accept",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        s5 = get_or_create_service(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-dns-service",
            description=f"DNS service for {tenant_label} office.",
            protocol="udp",
            port_start=53,
            port_end=53,
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r5.id, match_type="any", objects=[s5])

        f6=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-internal",
            description=f"Allow internal traffic for {tenant_label} office.",
        )[0]
        r6 = get_or_create_rule(
            actor=actor,
            filter=f6,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-allow-internal-rule",
            description=f"Allow internal traffic for {tenant_label} office.",
            action="accept",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        a2 = get_or_create_address(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-internal-network",
            description=f"Internal network for {tenant_label} office.",
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="192.168.0.0/16",
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r6.id, match_type="source", objects=[a2])

        f7=get_or_create_filter(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-deny-all",
            description=f"Deny all traffic for {tenant_label} office.",
        )[0]
        r7 = get_or_create_rule(
            actor=actor,
            filter=f7,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-deny-all-rule",
            description=f"Deny all traffic for {tenant_label} office.",
            action="deny",
            enable=True,
            log_type="log",
            hit_count=0,
            rule_sequence=1,
        )[0]
        a3 = get_or_create_address(
            actor=actor,
            tenant_id=target_tenant.id,
            name=f"{tenant_prefix}-all-network",
            description=f"All network for {tenant_label} office.",
            addr_type="network",
            ipv4_type="standard",
            ipv4Network="0.0.0.0/0",
        )[0]
        add_objects_to_rule(actor=actor, tenant_id=target_tenant.id, rule_id=r7.id, match_type="any", objects=[a3])


        tenant_filters = [f1, f2, f3, f4, f5, f6, f7]
        

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
            for i in range(3):  # Create 3 interfaces for each device
                interface_obj, _, _, _, _, _ = get_or_create_interface(
                    actor=actor,
                    tenant_id=target_tenant.id,
                    device_id=device_obj.id,
                    name=f"eth{i}",
                    description=f"Interface {i} for {device_obj.name}.",
                    type="physical",
                )
                created_interfaces.append(interface_obj)
                logger.info(f"Created {interface_obj} for device={device_obj.id} and tenant={target_tenant.id}")
            interface_obj, _, _, _, _, _ = get_or_create_interface(
                actor=actor,
                tenant_id=target_tenant.id,
                device_id=device_obj.id,
                name=f"vlan{20 if index % 2 == 0 else 30}",
                description=f"Vlan interface for {device_obj.name}.",
                type="vlan",
            )

            for i, filter in enumerate(tenant_filters):
                if i % 2 == 0: 
                    add_filter_to_interface(
                        actor=actor,
                        tenant_id=target_tenant.id,
                        interface_id=interface_obj.id,
                        filter_id=filter.id,
                        policy_sequence=3,
                        enable=True,
                        direction="in",
                    )
                else:
                    add_filter_to_interface(
                        actor=actor,
                        tenant_id=target_tenant.id,
                        interface_id=interface_obj.id,
                        filter_id=filter.id,
                        policy_sequence=4,
                        enable=True,
                        direction="out",
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
