import django.db.models as models

class AddressGroup(models.Model):
    tenant_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return f"AddressGroup(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')"

# class AddressGroup:
#     def __init__(self, id: int, tenant_id: int, name: str, description: str):
#         self.id = id
#         self.tenant_id = tenant_id
#         self.name = name
#         self.description = description
        
#     def __str__(self):
#         return f"AddressGroup(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')" 