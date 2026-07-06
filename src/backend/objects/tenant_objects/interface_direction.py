from django.db import models
from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class InterfaceDirection(TaggableMixin, models.Model):
    interface = models.ForeignKey("Interface", on_delete=models.CASCADE)
    direction = models.CharField(choices=[("in", "in"), ("out", "out")], max_length=3, default="in")

    def __str__(self):
        return f"InterfaceDirection(interface_id={self.interface_id}, direction='{self.direction}')"
