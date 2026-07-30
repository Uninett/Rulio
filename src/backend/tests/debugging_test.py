from backend.objects.tenant_objects.device import Device
from backend.objects.tenant_objects.device_group import DeviceGroup
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.debugging.add_test_data import create_interfaces_devices_devicegroups_tags


def test_create_interfaces_devices_devicegroups_tags_creates_data_for_ntnu_and_sikt(superuser, db):
    ntnu_tenant, _ = Tenant.objects.get_or_create(tenant_name="NTNU")
    sikt_tenant, _ = Tenant.objects.get_or_create(tenant_name="Sikt")

    create_interfaces_devices_devicegroups_tags(
        actor=superuser,
        tenant_id=ntnu_tenant.id,
        tenants=[ntnu_tenant, sikt_tenant],
    )

    assert Device.objects.filter(tenant=ntnu_tenant).exists()
    assert Device.objects.filter(tenant=sikt_tenant).exists()
    assert DeviceGroup.objects.filter(tenant=ntnu_tenant).exists()
    assert DeviceGroup.objects.filter(tenant=sikt_tenant).exists()
