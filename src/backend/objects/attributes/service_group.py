from django.db import models


class ServiceGroup(models.Model):
    tenant_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"ServiceGroup(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')"
