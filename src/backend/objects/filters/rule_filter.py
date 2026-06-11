from django.db import models

class RuleFilter(models.Model):
    rule_id = models.ForeignKey('Rule', on_delete=models.CASCADE)
    filter_id = models.ForeignKey('Filter', on_delete=models.CASCADE)
    sequnce = models.IntegerField()

# class RuleFilter:
#     def __init__(self, rule_id=None, rule_name=None, rule_type=None):
#         self.rule_id = rule_id
#         self.rule_name = rule_name
#         self.rule_type = rule_type

#     def __str__(self):
#         return f"RuleFilter(rule_id={self.rule_id}, rule_name={self.rule_name}, rule_type={self.rule_type})"