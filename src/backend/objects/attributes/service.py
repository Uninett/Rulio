from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    tenant_id = models.IntegerField()
    protocol = models.CharField(max_length=50)
    port_start = models.IntegerField()
    port_end = models.IntegerField()

    def __str__(self):
        return f"Service(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, protocol='{self.protocol}', port_start={self.port_start}, port_end={self.port_end})"
    

# class Service:
#     def __init__(self, id: int, name: str, description: str, tenant_id: int, protocol: str, port_start: int, port_end: int):
#         self.id = id
#         self.name = name
#         self.description = description
#         self.tenant_id = tenant_id
#         self.protocol = protocol
#         self.port_start = port_start
#         self.port_end = port_end

#     def __str__(self):
#         return f"Service(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, protocol='{self.protocol}', port_start={self.port_start}, port_end={self.port_end})"
