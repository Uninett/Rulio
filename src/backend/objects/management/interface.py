from django.db import models

class Interface(models.Model):
    device_id = models.ForeignKey('Device', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    VRF = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Interface(id={self.id}, device_id={self.device_id}, name='{self.name}', type='{self.type}', VRF='{self.VRF}', description='{self.description}')"

# class Interface:
#     def __init__(self, id: int, device_id: int, name: str, type: str, VRF: str, description: str):
#         self.id = id
#         self.device_id = device_id
#         self.name = name
#         self.type = type
#         self.VRF = VRF
#         self.description = description

#     def __str__(self):
#         return f"Interface(id={self.id}, device_id={self.device_id}, name='{self.name}', type='{self.type}', VRF='{self.VRF}', description='{self.description}')"