from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class RuleMatch(models.Model):
    MATCH_TYPE_CHOICES = [
        ("source", "Source"),
        ("destination", "Destination"),
        ("reverse_source", "Reverse Source"),
        ("reverse_destination", "Reverse Destination"),
    ]
    rule = models.ForeignKey("Rule", on_delete=models.CASCADE, related_name="matches")
    match = models.CharField(max_length=30, choices=MATCH_TYPE_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"RuleMatch(id={self.id}, rule_id={self.rule_id}, match={self.match}, object_type='{self.content_type}', object_id={self.object_id})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "match", "content_type", "object_id"],
                name="unique_rule_match_object",
            )
        ]
