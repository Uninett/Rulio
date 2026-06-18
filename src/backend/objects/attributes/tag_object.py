from django.db import models


class TagObject(models.Model):
    object_type = models.CharField(max_length=255)
    # TODO: object_id should maybe have an indicator of what type of object it is, we should have a way to determine the type of object
    object_id = models.IntegerField()
    tag_id = models.ForeignKey("Tag", on_delete=models.CASCADE)

    def __str__(self):
        return f"tag_object(tag_id={self.tag_id}, object_type='{self.object_type}', object_id={self.object_id})"
