from datetime import datetime
from django.db import models


class VersionControl(models.Model):
    filter_id = models.ForeignKey("Filter", on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    tenant_id = models.ForeignKey("Tenant", on_delete=models.CASCADE)

    def __str__(self):
        return f"VersionControl(id={self.id}, filter_id={self.filter_id}, datetime={self.datetime}, tenant_id={self.tenant_id})"


class VersionControl:
    def __init__(self, id: int, filter_id: int, datetime: datetime, tenant_id: int):
        self.id = id
        self.filter_id = filter_id
        self.datetime = datetime
        self.tenant_id = tenant_id
