from django.db import models
from pydantic import ValidationError


class Address(models.Model):
    TYPE_CHOICES = [
        ("standard", "Ip address that can be written with a subnet mask (e.g. 192.168.0.1/24)"),
        ("custom_range", "IP Range"),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()
    ipv4_type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    ipv6_type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    ipv4_value = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    ipv4_end = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    ipv6_value = models.GenericIPAddressField(protocol="IPv6", null=True, blank=True)
    ipv6_end = models.GenericIPAddressField(protocol="IPv6", null=True, blank=True)

    def clean(self):
        errors = {}

        if self.ipv4_type is None and self.ipv6_type is None:
            errors["type"] = "At least one of ipv4_type or ipv6_type must be set."

        if self.ipv4_type == "standard":
            if not self.ipv4_value:
                errors["ipv4_value"] = "IPv4 address is required."
            if self.ipv4_end:
                errors["ipv4_end"] = "End IPv4 address is not allowed for type 'standard', use 'custom_range' instead."
    
        elif self.ipv4_type == "custom_range":
            if not self.ipv4_value:
                errors["ipv4_value"] = "Start IPv4 address is required."
            if not self.ipv4_end:
                errors["ipv4_end"] = "End IPv4 address is required for an IPv4 custom range."

        if self.ipv6_type == "standard":
            if not self.ipv6_value:
                errors["ipv6_value"] = "IPv6 address is required."
            if self.ipv6_end:
                errors["ipv6_end"] = "End IPv6 address is not allowed for type 'standard', use 'custom_range' instead."


        elif self.ipv6_type == "custom_range":
            if not self.ipv6_value:
                errors["ipv6_value"] = "Start IPv6 address is required."
            if not self.ipv6_end:
                errors["ipv6_end"] = "End IPv6 address is required for an IPv6 custom range."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    
    def __str__(self):
        return (
            f"Address(id={self.id}, name='{self.name}', description='{self.description}', "
            f"\ntenant_id={self.tenant_id}, ipv4_type='{self.ipv4_type}', ipv6_type='{self.ipv6_type}', "
            f"\nipv4_value='{self.ipv4_value}', ipv4_end='{self.ipv4_end}', "
            f"\nipv6_value='{self.ipv6_value}', ipv6_end='{self.ipv6_end}')"
        )
    
    def get_address(self) -> list:
        addresses = []

        if self.ipv4_type == "standard":
            addresses.append(self.ipv4_value)
        elif self.ipv4_type == "custom_range":
            addresses.append([self.ipv4_value, self.ipv4_end])

        if self.ipv6_type == "standard":
            addresses.append(self.ipv6_value)
        elif self.ipv6_type == "custom_range":
            addresses.append([self.ipv6_value, self.ipv6_end])

        return addresses

