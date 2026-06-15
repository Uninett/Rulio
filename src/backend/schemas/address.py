from ninja import Schema
from ipaddress import IPv4Network, IPv6Network
from typing import Optional
from pydantic import Field, model_validator, ConfigDict


class CreateAddressSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    ipv4Address: Optional[IPv4Network] = Field(None, example="192.168.0.1/24")
    ipv4Address_end: Optional[IPv4Network] = Field(None, example="192.168.0.255/24")

    ipv6Address: Optional[IPv6Network] = Field(None, example="2001:db8::/32")
    ipv6Address_end: Optional[IPv6Network] = Field(None, example="2001:db8::ffff/32")

    type: str = Field(choices=["ipv4", "ipv6"], default="ipv4", example="ipv4")

    @model_validator(mode="after")
    def validate_at_least_one_ip(self):
        if self.ipv4Address is None and self.ipv6Address is None:
            raise ValueError("At least one of ipv4Address or ipv6Address is required")
        return self
