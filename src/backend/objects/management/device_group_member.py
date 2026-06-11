from django.db import models

class DeviceGroupMember(models.Model):
    device_id = models.ForeignKey('Device', on_delete=models.CASCADE)
    deviceGroup_id = models.ForeignKey('DeviceGroup', on_delete=models.CASCADE)

    def __str__(self):
        return f"DeviceGroupMember(device_id={self.device_id}, deviceGroup_id={self.deviceGroup_id})"

# class DeviceGroupMember:
#     def __init__(self, device_id: int, deviceGroup_id: int):
#         self.device_id = device_id
#         self.deviceGroup_id = deviceGroup_id

#     def __str__(self):
#         return f"DeviceGroupMember(device_id={self.device_id}, deviceGroup_id={self.deviceGroup_id})"