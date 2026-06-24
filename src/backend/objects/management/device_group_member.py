from django.db import models


class DeviceGroupMember(models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    device_group = models.ForeignKey("DeviceGroup", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["device", "device_group"], name="unique_device_group_member")]

    def __str__(self):
        return f"DeviceGroupMember(device_id={self.device_id}, device_group_id={self.device_group_id})"
