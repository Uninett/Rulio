from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from backend.objects.attributes.tag import Tag
from constants import GLOBAL_TENANT_ID


class TagConnection(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tagged_items")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.content_object and hasattr(self.content_object, "tenant_id"):
            if self.tag.tenant_id != self.content_object.tenant_id and self.tag.tenant_id != GLOBAL_TENANT_ID:
                raise ValidationError(
                    "Tag and tagged object must belong to the same tenant. Tag belongs to tenant_id {}, but tagged object belongs to tenant_id {}.".format(
                        self.tag.tenant_id, self.content_object.tenant_id
                    )
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tag", "content_type", "object_id"], name="unique_tag_per_object")
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
