from django.db import models

class TenantUserMember(models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    def __str__(self):
        return f"tenant_id: {self.tenant.id}, user_id: {self.user.id}"