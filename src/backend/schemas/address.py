
from ninja import Schema
from ipaddress import IPv4Address, IPv6Address
from typing import Optional
from pydantic import model_validator, ConfigDict

class CreateAddressSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: str
    ipv4Address: Optional[IPv4Address] = None
    ipv6Address: Optional[IPv6Address] = None
    type: str

    @model_validator(mode="after")
    def validate_at_least_one_ip(self):
        if self.ipv4Address is None and self.ipv6Address is None:
            raise ValueError("At least one of ipv4Address or ipv6Address is required")
        return self