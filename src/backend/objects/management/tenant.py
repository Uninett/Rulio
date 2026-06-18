from django.db import models


class Tenant(models.Model):
    tenant_name = models.CharField(max_length=255)

    def __str__(self):
        return f"tenant_id: {self.id}, tenant_name: {self.tenant_name}"


# class Tenant:
#     def __init__(self, tenant_id: str, tenant_name: str):
#         self.tenant_id = tenant_id
#         self.tenant_name = tenant_name

#     def __str__(self):
#         return f"tenant_id: {self.tenant_id}, tenant_name: {self.tenant_name}"
