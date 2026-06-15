import ipaddress
from django.db import models

class Address(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()
    type = models.CharField(max_length=10, choices=["ipv4", "ipv6"], lower=True)
    ipv4_value = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    ipv6_value = models.GenericIPAddressField(protocol='IPv6', null=True, blank=True)


    def __str__(self):
        return f"Address(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, type='{self.type}', ipv4_value='{self.ipv4_value}', ipv6_value='{self.ipv6_value}')"

    def get_address(self):
        if self.type == "ipv4":
            return ipaddress.IPv4Address(self.ipv4_value)
        elif self.type == "ipv6":
            return ipaddress.IPv6Address(self.ipv6_value)
        



