from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.interface import Interface
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.debugging.add_test_data import create_interfaces_devices_devicegroups_tags


def test_create_interfaces_devices_devicegroups_tags_creates_data_for_ntnu(superuser, db):
    gløshaugen_1_tenant, _ = Tenant.objects.get_or_create(tenant_name="Gløshaugen 1")
    gløshaugen_2_tenant, _ = Tenant.objects.get_or_create(tenant_name="Gløshaugen 2")
    dragvoll_tenant, _ = Tenant.objects.get_or_create(tenant_name="Dragvoll")
    kalvskinnet_tenant, _ = Tenant.objects.get_or_create(tenant_name="Kalvskinnet")

    create_interfaces_devices_devicegroups_tags(
        actor=superuser,
        tenant_id=gløshaugen_1_tenant.id,
        tenants=[gløshaugen_1_tenant, gløshaugen_2_tenant, dragvoll_tenant, kalvskinnet_tenant],
    )

    assert Device.objects.filter(tenant=gløshaugen_1_tenant).exists()
    assert Device.objects.filter(tenant=gløshaugen_2_tenant).exists()
    assert Device.objects.filter(tenant=dragvoll_tenant).exists()
    assert Device.objects.filter(tenant=kalvskinnet_tenant).exists()
    assert DeviceGroup.objects.filter(tenant=gløshaugen_1_tenant).exists()
    assert DeviceGroup.objects.filter(tenant=gløshaugen_2_tenant).exists()
    assert DeviceGroup.objects.filter(tenant=dragvoll_tenant).exists()
    assert DeviceGroup.objects.filter(tenant=kalvskinnet_tenant).exists()


def test_create_interfaces_devices_devicegroups_tags_can_run_twice(superuser, db):
    gløshaugen_1_tenant, _ = Tenant.objects.get_or_create(tenant_name="Gløshaugen 1")
    gløshaugen_2_tenant, _ = Tenant.objects.get_or_create(tenant_name="Gløshaugen 2")
    dragvoll_tenant, _ = Tenant.objects.get_or_create(tenant_name="Dragvoll")
    kalvskinnet_tenant, _ = Tenant.objects.get_or_create(tenant_name="Kalvskinnet")
    tenants = [gløshaugen_1_tenant, gløshaugen_2_tenant, dragvoll_tenant, kalvskinnet_tenant]

    create_interfaces_devices_devicegroups_tags(actor=superuser, tenant_id=gløshaugen_1_tenant.id, tenants=tenants)
    interface_count = Interface.objects.count()

    create_interfaces_devices_devicegroups_tags(actor=superuser, tenant_id=gløshaugen_1_tenant.id, tenants=tenants)

    assert Interface.objects.count() == interface_count


def test_create_interfaces_devices_devicegroups_tags_can_run_after_device_is_edited(superuser, db):
    gløshaugen_1_tenant, _ = Tenant.objects.get_or_create(tenant_name="Gløshaugen 1")
    gløshaugen_2_tenant, _ = Tenant.objects.get_or_create(tenant_name="Gløshaugen 2")
    dragvoll_tenant, _ = Tenant.objects.get_or_create(tenant_name="Dragvoll")
    kalvskinnet_tenant, _ = Tenant.objects.get_or_create(tenant_name="Kalvskinnet")
    tenants = [gløshaugen_1_tenant, gløshaugen_2_tenant, dragvoll_tenant, kalvskinnet_tenant]

    create_interfaces_devices_devicegroups_tags(actor=superuser, tenant_id=gløshaugen_1_tenant.id, tenants=tenants)
    Device.objects.filter(name="gløshaugen-1-edge-fw-02").update(description="Edited in the UI.")
    device_count = Device.objects.count()

    create_interfaces_devices_devicegroups_tags(actor=superuser, tenant_id=gløshaugen_1_tenant.id, tenants=tenants)

    assert Device.objects.count() == device_count
