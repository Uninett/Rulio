from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Rule(TaggableMixin, models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    log_type = models.CharField(max_length=255)
    hit_count = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField()
    changed_by = models.IntegerField()
    enable = models.BooleanField(default=True)

    def __str__(self):
        return f"Rule(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, action='{self.action}', log_type='{self.log_type}', hit_count={self.hit_count}, date_created='{self.date_created}', date_changed='{self.date_changed}', created_by={self.created_by}, changed_by={self.changed_by}, enable={self.enable})"

    def increment_hit_count(self):
        self.hit_count += 1
        self.save(update_fields=["hit_count"])
