from django.db import models


class Interface(models.Model):
    device_id = models.ForeignKey("Device", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    VRF = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Interface(id={self.id}, device_id={self.device_id}, name='{self.name}', type='{self.type}', VRF='{self.VRF}', description='{self.description}')"
