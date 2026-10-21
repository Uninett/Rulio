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
        # Deferred, so the constraint is checked when the transaction commits instead of after each row.
        # This lets interface names be swapped within one save.
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["device", "name"],
                name="unique_interface_name_per_device",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]

    def __str__(self):
        return f"Interface(id={self.id}, device_id={self.device_id}, name='{self.name}', type='{self.type}', VRF='{self.VRF}', description='{self.description}')"
