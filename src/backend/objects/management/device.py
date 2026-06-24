from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Device(TaggableMixin, models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255)
    platform = models.CharField(max_length=255)
    model = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"device(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', vendor='{self.vendor}', platform='{self.platform}', model='{self.model}', role='{self.role}', description='{self.description}')"
