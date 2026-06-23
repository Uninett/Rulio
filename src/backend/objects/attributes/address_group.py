import django.db.models as models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class AddressGroup(TaggableMixin, models.Model):
    tenant_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    addr_type = models.CharField(max_length=20, default="Group", editable=False)

    def __str__(self):
        return (
            f"AddressGroup(id={self.id}, tenant_id={self.tenant_id}, type='{self.addr_type}', "
            f"name='{self.name}', description='{self.description}')"
        )

    def save(self, *args, **kwargs):
        self.addr_type = "Group"
        super().save(*args, **kwargs)
