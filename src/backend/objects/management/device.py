from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Device(TaggableMixin, models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Device(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', platform='{self.platform}', type='{self.type}', description='{self.description}')"
