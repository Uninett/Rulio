from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()

    def __str__(self):
        return f"tag(id={self.id}, name={self.name}, description={self.description}, tenant_id={self.tenant_id})"
