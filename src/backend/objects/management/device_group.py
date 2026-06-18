from django.db import models


class DeviceGroup(models.Model):
    tenant_id = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"device_group(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')"


# class DeviceGroup:
#     def __init__(self, id: int, tenant_id: int, name: str, description: str):
#         self.id = id
#         self.tenant_id = tenant_id
#         self.name = name
#         self.description = description

#     def __str__(self):
#         return f"device_group(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')"
