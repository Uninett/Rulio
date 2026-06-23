from django.db import models


class RuleMatch(models.Model):
    MATCH_TYPE_CHOICES = [
        ("Source", "Source"),
        ("Destination", "Destination"),
        ("Reverse_Source", "Reverse Source"),
        ("Reverse_Destination", "Reverse Destination"),
    ]
    rule_id = models.IntegerField()
    match = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES)
    object_type = models.CharField(max_length=255)
    object_id = models.ForeignKey("Rule", on_delete=models.CASCADE)

    def __str__(self):
        return f"RuleMatch(id={self.id}, rule_id={self.rule_id}, match={self.match}, object_type='{self.object_type}', object_id={self.object_id})"
