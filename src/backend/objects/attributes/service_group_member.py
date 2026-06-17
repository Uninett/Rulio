from django.db import models


class ServiceGroupMember(models.Model):
    group = models.ForeignKey("ServiceGroup", on_delete=models.CASCADE)
    service = models.ForeignKey("Service", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["group", "service"], name="unique_group_service")]


# class ServiceGroupMember:
#     def __init__(self, group_id: int, service_id: int):
#         self.group_id = group_id
#         self.service_id = service_id

#     def __str__(self):
#         return f"ServiceGroupMember(group_id={self.group_id}, service_id={self.service_id})"
