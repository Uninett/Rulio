from django.db import models

class ServiceGroup(models.Model):
    tennant_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"ServiceGroup(id={self.id}, tennant_id={self.tennant_id}, name='{self.name}', description='{self.description}')"
    

# class ServiceGroup:
#     def __init__(self, id: int, tennant_id: int, name: str, description: str = ""):
#         self.id = id
#         self.tennant_id = tennant_id
#         self.name = name
#         self.description = description

#     def __str__(self):
#         return f"ServiceGroup(id={self.id}, tennant_id={self.tennant_id}, name='{self.name}', description='{self.description}')"