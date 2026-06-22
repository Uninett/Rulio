from django.db import models


class Service(models.Model):
    PROTOCOL_CHOICES = [
        ("TCP", "TCP"),
        ("UDP", "UDP"),
        ("ICMP", "ICMP"),
        ("ICMPv6", "ICMPv6"),
        ("GRE", "GRE"),
        ("ESP", "ESP"),
        ("AH", "AH"),
        ("IP", "IP"),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()
    protocol = models.CharField(max_length=50, choices=PROTOCOL_CHOICES)
    port_start = models.IntegerField(null=True, blank=True)
    port_end = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Service(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, protocol='{self.protocol.upper()}', port_start={self.port_start}, port_end={self.port_end})"

    def get_ports(self):
        if self.port_start is None and self.port_end is None:
            return None
        elif self.port_start == self.port_end:
            return str(self.port_start)
        else:
            return f"{self.port_start}-{self.port_end}"

    def get_protocol(self):
        return self.protocol.lower()

    def is_port_based(self):
        if self.protocol.upper() in ["TCP", "UDP"]:
            return True
        return False
    
 