import django.db.models as models

class AddressGroupMember(models.Model):
    group_id = models.ForeignKey('AddressGroup', on_delete=models.CASCADE)
    address_id = models.ForeignKey('Address', on_delete=models.CASCADE)

    def __str__(self):
        return f"AddressGroupMember(group_id={self.group_id}, address_id={self.address_id})"

# class AddressGroupMember:
#     def __init__(self, group_id: int, address_id: int):
#         self.group_id = group_id
#         self.address_id = address_id

#     def __str__(self):
#         return f"AddressGroupMember(group_id={self.group_id}, address_id={self.address_id})"