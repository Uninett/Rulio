from django.db import models


class RuleFilter(models.Model):
    rule = models.ForeignKey("Rule", on_delete=models.CASCADE)
    filter = models.ForeignKey("Filter", on_delete=models.CASCADE)
    sequence = models.IntegerField()
