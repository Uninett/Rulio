from django.conf import settings
from django.db import models


# Unsaved changes a user has made on a page, kept until they are saved or discarded.
# scope names what is being edited (e.g. "filter_rules") and scope_id which one (e.g. the filter id).
# The structure of changes is defined by the code that owns the scope.
class Draft(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="drafts")
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE, related_name="drafts")
    scope = models.CharField(max_length=64)
    scope_id = models.PositiveIntegerField()
    changes = models.JSONField(default=dict)
    date_created = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "scope", "scope_id"), name="unique_draft_per_user_scope"),
        ]

    def __str__(self):
        return f"Draft(id={self.id}, user_id={self.user_id}, tenant_id={self.tenant_id}, scope='{self.scope}', scope_id={self.scope_id})"
