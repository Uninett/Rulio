from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class ServiceGroup(TaggableMixin, models.Model):
    tenant_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    service_type = models.CharField(max_length=20, default="Group", editable=False)

    def __str__(self):
        return f"ServiceGroup(id={self.id}, tenant_id={self.tenant_id}, type='{self.service_type}', name='{self.name}', description='{self.description}')"
