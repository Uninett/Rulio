from django.db import models

class Filter(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()
    enable = models.BooleanField(default=True)

    def __str__(self):
        return f"filter(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, enable={self.enable})"

# class RuleFilter:
#     def __init__(self, rule_id=None, rule_name=None, rule_type=None):
#         self.rule_id = rule_id
#         self.rule_name = rule_name
#         self.rule_type = rule_type

#     def __str__(self):
#         return f"RuleFilter(rule_id={self.rule_id}, rule_name={self.rule_name}, rule_type={self.rule_type})"