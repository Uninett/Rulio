from typing import ClassVar

from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Interface(TaggableMixin, models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True, blank=True)
    VRF = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["device", "name"], name="unique_interface_name_per_device"),
        ]

    def __str__(self):
        return f"Interface(id={self.id}, device_id={self.device_id}, name='{self.name}', type='{self.type}', VRF='{self.VRF}', description='{self.description}')"
