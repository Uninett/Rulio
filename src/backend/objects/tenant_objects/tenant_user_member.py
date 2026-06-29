from django.db import models


class TenantUserMember(models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    class TenantRole(models.TextChoices):
        MEMBER = "member", "Member"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=30, choices=TenantRole.choices)

    class Meta:
        unique_together = ("user", "tenant")

    def __str__(self):
        return f"tenant_id: {self.tenant.id}, user_id: {self.user.id}"
