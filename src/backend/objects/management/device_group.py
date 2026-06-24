from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class DeviceGroup(TaggableMixin, models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"device_group(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')"
