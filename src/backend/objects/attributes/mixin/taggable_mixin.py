from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from backend.objects.attributes.tag import Tag
from backend.objects.attributes.tag_connection import TagConnection


class TaggableMixin(models.Model):
    tag_objects = GenericRelation(TagConnection, related_query_name="%(app_label)s_%(class)s")

    class Meta:
        abstract = True

    def get_tags(self):
        return Tag.objects.filter(tagged_items__in=self.tag_objects.all()).distinct()

    def add_tag(self, tag):
        if hasattr(self, "tenant_id") and tag.tenant_id != self.tenant_id:
            raise ValueError("Tag and object must belong to the same tenant.")

        tag_object, created = self.tag_objects.get_or_create(tag=tag)
        return tag_object, created

    def remove_tag(self, tag):
        deleted_count, _ = self.tag_objects.filter(tag=tag).delete()
        return deleted_count

    def has_tag(self, tag):
        return self.tag_objects.filter(tag=tag).exists()

    def clear_tags(self):
        deleted_count, _ = self.tag_objects.all().delete()
        return deleted_count
