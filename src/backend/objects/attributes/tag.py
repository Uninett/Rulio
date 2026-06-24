from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)

    def __str__(self):
        return f"Tag(id={self.id}, name={self.name}, description={self.description}, tenant_id={self.tenant_id})"
