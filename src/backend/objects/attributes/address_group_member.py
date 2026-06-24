import django.db.models as models


class AddressGroupMember(models.Model):
    group = models.ForeignKey("AddressGroup", on_delete=models.CASCADE)
    address = models.ForeignKey("Address", on_delete=models.CASCADE)

    def __str__(self):
        return f"AddressGroupMember(group_id={self.group_id}, address_id={self.address_id})"
