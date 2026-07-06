from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin
from backend.objects.filters.filter import Filter
from backend.objects.tenant_objects.tenant import Tenant


class Rule(TaggableMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE, related_name="rules")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="rules"
    )
    action = models.CharField(max_length=255, blank=True, null=True)
    enable = models.BooleanField(default=True)
    rule_sequence = models.PositiveIntegerField(default=0)
    log_type = models.CharField(max_length=255, blank=True, null=True)
    hit_count = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    changed_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Rule(id={self.id}, name='{self.name}', description='{self.description}', filter_id={self.filter_id}, tenant_id={self.tenant_id}, action='{self.action}', enable={self.enable}, rule_sequence={self.rule_sequence}, log_type='{self.log_type}', hit_count={self.hit_count}, date_created='{self.date_created}', date_changed='{self.date_changed}', created_by='{self.created_by}', changed_by='{self.changed_by}')"

