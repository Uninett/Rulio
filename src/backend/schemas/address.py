from ninja import Schema
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from typing import Optional, Literal
from pydantic import Field, model_validator, ConfigDict


class CreateAddressSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    ipv4Network: Optional[IPv4Network] = Field(None, example="192.168.0.0/24")
    ipv4Address_start: Optional[IPv4Address] = Field(None, example=None)
    ipv4Address_end: Optional[IPv4Address] = Field(None, example=None)

    ipv6Network: Optional[IPv6Network] = Field(None, example="2001:db8::/32")
    ipv6Address_start: Optional[IPv6Address] = Field(None, example=None)
    ipv6Address_end: Optional[IPv6Address] = Field(None, example=None)

    ipv4_type: Optional[Literal["standard", "custom_range"]] = None
    ipv6_type: Optional[Literal["standard", "custom_range"]] = None

    
    @model_validator(mode="after")
    def validate_ip_ranges(self):

        if self.ipv4_type is None and self.ipv6_type is None:
            raise ValueError("At least one of ipv4_type or ipv6_type must be set.")
        
        if self.ipv4_type is None:
            if self.ipv4Network is not None or self.ipv4Address_start is not None or self.ipv4Address_end is not None:
                raise ValueError("ipv4Network, ipv4Address_start, and ipv4Address_end must be null if ipv4_type is not set.")

        if self.ipv6_type is None:
            if self.ipv6Network is not None or self.ipv6Address_start is not None or self.ipv6Address_end is not None:
                raise ValueError("ipv6Network, ipv6Address_start, and ipv6Address_end must be null if ipv6_type is not set.")


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
