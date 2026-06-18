from django.db import models


class DeviceGroupMember(models.Model):
    device_id = models.ForeignKey("Device", on_delete=models.CASCADE)
    deviceGroup_id = models.ForeignKey("DeviceGroup", on_delete=models.CASCADE)

    def __str__(self):
        return f"DeviceGroupMember(device_id={self.device_id}, deviceGroup_id={self.deviceGroup_id})"
