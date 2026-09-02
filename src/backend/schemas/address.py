from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Literal

from ninja import Schema
from pydantic import ConfigDict, Field, model_validator


class CreateAddressSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    ipv4Network: IPv4Network | None = Field(None, json_schema_extra={"example": "192.168.0.0/24"})
    ipv4Address_start: IPv4Address | None = Field(None, json_schema_extra={"example": None})
    ipv4Address_end: IPv4Address | None = Field(None, json_schema_extra={"example": None})

    ipv6Network: IPv6Network | None = Field(None, json_schema_extra={"example": "2001:db8::/32"})
    ipv6Address_start: IPv6Address | None = Field(None, json_schema_extra={"example": None})
    ipv6Address_end: IPv6Address | None = Field(None, json_schema_extra={"example": None})

    addr_type: Literal["host", "network", "range"] = Field(..., json_schema_extra={"example": "network"})
    ipv4_type: Literal["standard", "custom_range"] | None = None
    ipv6_type: Literal["standard", "custom_range"] | None = None

    @model_validator(mode="after")
    def validate_ip_ranges(self):

        if self.ipv4_type is None and self.ipv6_type is None:
            raise ValueError("At least one of ipv4_type or ipv6_type must be set.")

        if self.ipv4_type is None:
            if self.ipv4Network is not None or self.ipv4Address_start is not None or self.ipv4Address_end is not None:
                raise ValueError(
                    "ipv4Network, ipv4Address_start, and ipv4Address_end must be null if ipv4_type is not set."
                )

        if self.ipv6_type is None:
            if self.ipv6Network is not None or self.ipv6Address_start is not None or self.ipv6Address_end is not None:
                raise ValueError(
                    "ipv6Network, ipv6Address_start, and ipv6Address_end must be null if ipv6_type is not set."
                )

        if self.ipv4_type == "standard":
            if self.ipv4Network is None:
                raise ValueError("ipv4Network is required for type 'standard'")
            if self.ipv4Address_start is not None or self.ipv4Address_end is not None:
                raise ValueError("ipv4Address_start and ipv4Address_end must be null for type 'standard'")

        elif self.ipv4_type == "custom_range":
            if self.ipv4Address_start is None:
                raise ValueError("ipv4Address_start is required for type 'custom_range'")
            if self.ipv4Address_end is None:
                raise ValueError("ipv4Address_end is required for type 'custom_range'")
            if self.ipv4Network is not None:
                raise ValueError("ipv4Network must be null for type 'custom_range'")

            if self.ipv4Address_end < self.ipv4Address_start:
                raise ValueError("ipv4Address_end must be greater than or equal to ipv4Address_start")

        if self.ipv6_type == "standard":
            if self.ipv6Network is None:
                raise ValueError("ipv6Network is required for type 'standard'")
            if self.ipv6Address_start is not None or self.ipv6Address_end is not None:
                raise ValueError("ipv6Address_start and ipv6Address_end must be null for type 'standard'")

        elif self.ipv6_type == "custom_range":
            if self.ipv6Address_start is None:
                raise ValueError("ipv6Address_start is required for type 'custom_range'")
            if self.ipv6Address_end is None:
                raise ValueError("ipv6Address_end is required for type 'custom_range'")
            if self.ipv6Network is not None:
                raise ValueError("ipv6Network must be null for type 'custom_range'")

            if self.ipv6Address_end < self.ipv6Address_start:
                raise ValueError("ipv6Address_end must be greater than or equal to ipv6Address_start")

        return self
