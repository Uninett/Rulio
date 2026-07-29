from django.core.exceptions import ValidationError
from django.db import models

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Service(TaggableMixin, models.Model):
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

    ICMP_PROTOCOLS = {"ICMP", "ICMPV6"}
    PORT_PROTOCOLS = {"TCP", "UDP"}

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    protocol = models.CharField(max_length=50, choices=PROTOCOL_CHOICES)
    port_start = models.IntegerField(null=True, blank=True)
    port_end = models.IntegerField(null=True, blank=True)
    icmp_type = models.PositiveSmallIntegerField(null=True, blank=True)
    icmp_code = models.PositiveSmallIntegerField(null=True, blank=True)
    service_type = models.CharField(max_length=20, default="Service", editable=False)

    def __str__(self):
        return (
            f"Service(id={self.id}, tenant_id={self.tenant_id}, type='{self.service_type}', "
            f"name='{self.name}', description='{self.description}', protocol='{self.protocol.upper()}', "
            f"port_start={self.port_start}, port_end={self.port_end}, "
            f"icmp_type={self.icmp_type}, icmp_code={self.icmp_code})"
        )

    def clean(self):
        super().clean()

        protocol = self.protocol.upper().strip()

        if protocol in self.PORT_PROTOCOLS:
            if self.icmp_type is not None or self.icmp_code is not None:
                raise ValidationError("ICMP type/code can only be set for ICMP or ICMPv6 services.")

            if self.port_start is None and self.port_end is None:
                return

            if self.port_start is None or self.port_end is None:
                raise ValidationError("Both port_start and port_end must be set together.")

            if not (0 <= self.port_start <= 65535 and 0 <= self.port_end <= 65535):
                raise ValidationError("Ports must be between 0 and 65535.")

            if self.port_start > self.port_end:
                raise ValidationError("port_start cannot be greater than port_end.")

            return

        if protocol in self.ICMP_PROTOCOLS:
            if self.port_start is not None or self.port_end is not None:
                raise ValidationError("Ports cannot be set for ICMP or ICMPv6 services.")

            if self.icmp_code is not None and self.icmp_type is None:
                raise ValidationError("icmp_code cannot be set without icmp_type.")

            if self.icmp_type is not None and not (0 <= self.icmp_type <= 255):
                raise ValidationError("icmp_type must be between 0 and 255.")

            if self.icmp_code is not None and not (0 <= self.icmp_code <= 255):
                raise ValidationError("icmp_code must be between 0 and 255.")

            return

        if self.port_start is not None or self.port_end is not None:
            raise ValidationError(f"Ports cannot be set for protocol {protocol}.")

        if self.icmp_type is not None or self.icmp_code is not None:
            raise ValidationError(f"ICMP type/code cannot be set for protocol {protocol}.")

    def get_ports(self):
        if self.port_start is None and self.port_end is None:
            return None
        if self.port_start == self.port_end:
            return str(self.port_start)
        return f"{self.port_start}-{self.port_end}"

    def get_protocol(self):
        return self.protocol.strip().lower()

    def get_icmp_type(self):
        return self.icmp_type

    def get_icmp_code(self):
        return self.icmp_code

    def is_port_based(self):
        return self.protocol.upper() in self.PORT_PROTOCOLS

    def is_icmp_based(self):
        return self.protocol.upper() in self.ICMP_PROTOCOLS
