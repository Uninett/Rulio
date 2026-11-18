from typing import ClassVar

from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin
from backend.services.config_generation.platform_capabilities import PLATFORM_CAPABILITIES

PLATFORM_CHOICES = [(platform, platform) for platform in PLATFORM_CAPABILITIES]


class Device(TaggableMixin, models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=255, choices=PLATFORM_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_device_name_per_tenant",
                violation_error_message="A device with this name already exists.",
            ),
            models.CheckConstraint(
                condition=models.Q(platform__in=list(PLATFORM_CAPABILITIES)),
                name="device_platform_valid",
                violation_error_message="Invalid platform.",
            ),
        ]

    def __str__(self):
        return f"Device(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', platform='{self.platform}', description='{self.description}')"
