from django.db import models


class ServiceGroupMember(models.Model):
    group = models.ForeignKey("ServiceGroup", on_delete=models.CASCADE)
    service = models.ForeignKey("Service", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["group", "service"], name="unique_group_service")]
