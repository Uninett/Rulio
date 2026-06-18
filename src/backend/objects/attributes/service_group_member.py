from django.db import models


class ServiceGroupMember(models.Model):
    group_id = models.ForeignKey("ServiceGroup", on_delete=models.CASCADE)
    service_id = models.ForeignKey("Service", on_delete=models.CASCADE)
