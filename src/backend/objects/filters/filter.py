from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Filter(TaggableMixin, models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()
    enable = models.BooleanField(default=True)

    def __str__(self):
        return f"filter(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, enable={self.enable})"
