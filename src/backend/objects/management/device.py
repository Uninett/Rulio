from django.db import models

class Device(models.Model):
    tenant_id = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Device(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', platform='{self.platform}', type='{self.type}', description='{self.description}')"

# class Device:
#     def __init__(self, id:int, tenant_id: int, name: str, platform:str, type:str, description: str):
#         self.id = id
#         self.tenant_id = tenant_id
#         self.name = name
#         self.platform = platform
#         self.type = type
#         self.description = description

#     def __str__(self):
#         return f"Device(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', platform='{self.platform}', type='{self.type}', description='{self.description}')"