from datetime import datetime
from django.db import models

class Rule(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.ForeignKey('Tenant', on_delete=models.CASCADE)
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


# class Rule:

#     def __init__(self, id: int, name: str, description: str, tennant_id: int, action: str, log_type: str, hit_count: int, date_created: datetime, date_changed: datetime, created_by: int, changed_by: int, enable: bool):
#         self.id = id
#         self.name = name
#         self.description = description
#         self.tennant_id = tennant_id
#         self.action = action
#         self.log_type = log_type
#         self.hit_count = hit_count
#         self.date_created = date_created
#         self.date_changed = date_changed
#         self.created_by = created_by
#         self.changed_by = changed_by
#         self.enable = enable

#     def __str__(self):
#         return f"Rule(id={self.id}, name='{self.name}', description='{self.description}', tennant_id={self.tennant_id}, action='{self.action}', log_type='{self.log_type}', hit_count={self.hit_count}, date_created='{self.date_created}', date_changed='{self.date_changed}', created_by={self.created_by}, changed_by={self.changed_by}, enable={self.enable})"