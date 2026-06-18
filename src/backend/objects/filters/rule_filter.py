from django.db import models


class RuleFilter(models.Model):
    rule_id = models.ForeignKey("Rule", on_delete=models.CASCADE)
    filter_id = models.ForeignKey("Filter", on_delete=models.CASCADE)
    sequnce = models.IntegerField()
