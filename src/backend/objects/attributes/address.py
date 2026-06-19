from django.core.exceptions import ValidationError
from django.db import models
from ipaddress import summarize_address_range, IPv4Address, IPv6Address, IPv4Network, IPv6Network

from backend.objects.attributes.mixin.taggable_mixin import TaggableMixin


class Address(TaggableMixin, models.Model):
    """
    Model representing an IP address or range, which can be either IPv4 or IPv6.
    The model supports two types of addresses: 'standard', which is a single IP address or a network in CIDR notation,
    and 'custom_range', which is defined by a start and end IP address.
    \nFields:
    \nname (str): The name of the address.
    \ndescription (str): A description of the address.
    \ntenant_id (int): The ID of the tenant to which this address belongs.
    \nipv4_type (str): The type of the IPv4 address, either 'standard' or 'custom_range'.
    \nipv6_type (str): The type of the IPv6 address, either 'standard' or 'custom_range'.
    \nipv4Network (str): The IPv4 network in CIDR notation
    \nipv6Network (str): The IPv6 network in CIDR notation.
    \nipv4Address_start (str): The starting IPv4 address for a custom range.
    \nipv4Address_end (str): The ending IPv4 address for a custom range.
    \nipv6Address_start (str): The starting IPv6 address for a custom range.
    \nipv6Address_end (str): The ending IPv6 address for a custom range.
    """

    TYPE_CHOICES = [
        ("standard", "Ip address that can be written with a subnet mask (e.g. 192.168.0.1/24)"),
        ("custom_range", "IP Range"),
    ]
    ADDR_TYPE_CHOICES = [
        ("host", "Host"),
        ("network", "Network"),
        ("range", "Range"),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tenant_id = models.IntegerField()
    addr_type = models.CharField(max_length=20, choices=ADDR_TYPE_CHOICES, default="host")
    ipv4_type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    ipv6_type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    ipv4Network = models.CharField(max_length=50, null=True, blank=True)
    ipv6Network = models.CharField(max_length=100, null=True, blank=True)
    ipv4Address_start = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    ipv4Address_end = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    ipv6Address_start = models.GenericIPAddressField(protocol="IPv6", null=True, blank=True)
    ipv6Address_end = models.GenericIPAddressField(protocol="IPv6", null=True, blank=True)

    def clean(self):
        errors = {}
        # Validate that at least one of ipv4_type or ipv6_type is set
        if self.ipv4_type is None and self.ipv6_type is None:
            errors["ipv4_type"] = "At least one of ipv4_type or ipv6_type must be set."
            errors["ipv6_type"] = "At least one of ipv4_type or ipv6_type must be set."
        if self.ipv4_type is None:
            if self.ipv4Network or self.ipv4Address_start or self.ipv4Address_end:
                errors["ipv4_type"] = (
                    "ipv4Network, ipv4Address_start, and ipv4Address_end must be null if ipv4_type is not set."
                )
        if self.ipv6_type is None:
            if self.ipv6Network or self.ipv6Address_start or self.ipv6Address_end:
                errors["ipv6_type"] = (
                    "ipv6Network, ipv6Address_start, and ipv6Address_end must be null if ipv6_type is not set."
                )

        # Validate IPv4 standard
        if self.ipv4_type == "standard":
            if not self.ipv4Network:
                errors["ipv4Network"] = "IPv4 network is required for type 'standard'."
            if self.ipv4Address_start or self.ipv4Address_end:
                errors["ipv4Address_start"] = (
                    "ipv4Address_start/end are not allowed for type 'standard', use 'custom_range' instead."
                )

            if self.ipv4Network:
                try:
                    IPv4Network(self.ipv4Network)
                except ValueError:
                    errors["ipv4Network"] = "Invalid IPv4 network format. Expected format is 'x.x.x.x/y'."

        # Validate IPv4 custom range
        elif self.ipv4_type == "custom_range":
            if not self.ipv4Address_start:
                errors["ipv4Address_start"] = "Start IPv4 address is required."
            if not self.ipv4Address_end:
                errors["ipv4Address_end"] = "End IPv4 address is required for an IPv4 custom range."
            if self.ipv4Network:
                errors["ipv4Network"] = "ipv4Network must be null for type 'custom_range'."

            if (
                self.ipv4Address_start
                and self.ipv4Address_end
                and IPv4Address(self.ipv4Address_start) > IPv4Address(self.ipv4Address_end)
            ):
                errors["ipv4Address_end"] = "Start IPv4 address must be less than or equal to end IPv4 address."

        # Validate IPv6 standard
        if self.ipv6_type == "standard":
            if not self.ipv6Network:
                errors["ipv6Network"] = "IPv6 network is required for type 'standard'."
            if self.ipv6Address_start or self.ipv6Address_end:
                errors["ipv6Address_start"] = (
                    "ipv6Address_start/end are not allowed for type 'standard', use 'custom_range' instead."
                )
            if self.ipv6Network:
                try:
                    IPv6Network(self.ipv6Network)
                except ValueError:
                    errors["ipv6Network"] = "Invalid IPv6 network format. Expected format is 'x:x:x:x:x:x:x:x/y'."

        # Validate IPv6 custom range
        elif self.ipv6_type == "custom_range":
            if not self.ipv6Address_start:
                errors["ipv6Address_start"] = "Start IPv6 address is required."
            if not self.ipv6Address_end:
                errors["ipv6Address_end"] = "End IPv6 address is required for an IPv6 custom range."
            if self.ipv6Network:
                errors["ipv6Network"] = "ipv6Network must be null for type 'custom_range'."
            if (
                self.ipv6Address_start
                and self.ipv6Address_end
                and IPv6Address(self.ipv6Address_start) > IPv6Address(self.ipv6Address_end)
            ):
                errors["ipv6Address_end"] = "Start IPv6 address must be less than or equal to end IPv6 address."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Address(id={self.id}, name='{self.name}', description='{self.description}', "
            f"\ntenant_id={self.tenant_id}, ipv4_type='{self.ipv4_type}', ipv6_type='{self.ipv6_type}', "
            f"\nipv4Network='{self.ipv4Network}', ipv6Network='{self.ipv6Network}', "
            f"\nipv4Address_start='{self.ipv4Address_start}', ipv4Address_end='{self.ipv4Address_end}', "
            f"\nipv6Address_start='{self.ipv6Address_start}', ipv6Address_end='{self.ipv6Address_end}')"
        )

    def get_address(self) -> tuple[list[IPv4Network], list[IPv6Network]]:
        ipv4_addresses = []
        ipv6_addresses = []

        if self.ipv4_type == "standard":
            ipv4_addresses = [IPv4Network(self.ipv4Network)]
        elif self.ipv4_type == "custom_range":
            ipv4_addresses = list(
                summarize_address_range(IPv4Address(self.ipv4Address_start), IPv4Address(self.ipv4Address_end))
            )

        if self.ipv6_type == "standard":
            ipv6_addresses = [IPv6Network(self.ipv6Network)]
        elif self.ipv6_type == "custom_range":
            ipv6_addresses = list(
                summarize_address_range(IPv6Address(self.ipv6Address_start), IPv6Address(self.ipv6Address_end))
            )

        return ipv4_addresses, ipv6_addresses
