from ninja import Schema, Field
from typing import Optional
from pydantic import model_validator, ConfigDict


class CreateServiceSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    protocol: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "TCP"})
    port_start: Optional[int] = Field(None, json_schema_extra={"example": 80}, ge=1, le=65535)
    port_end: Optional[int] = Field(None, json_schema_extra={"example": 80}, ge=1, le=65535)

    @model_validator(mode="after")
    def validate_ports(self):
        # If port_end is not provided, set it to the same value as port_start

        if self.port_end is None and self.port_start is not None:
            self.port_end = self.port_start
        if self.port_end < self.port_start and self.port_end is not None and self.port_start is not None:
            raise ValueError("port_end must be greater than or equal to port_start")
        return self

    # Should we include protocol validation? If so the network admin should probably be able to configure these themselves,
    # so if we want to add this validation, we should make the list of valid protocols be configureable.
    @model_validator(mode="after")
    def validate_protocol(self):
        self.protocol = self.protocol.upper()
        return self

        # valid_protocols = {"TCP", "UDP", "ICMP"}
        # if self.protocol not in valid_protocols:
        #     raise ValueError(f"Invalid protocol: {self.protocol}. Valid options are: {', '.join(valid_protocols)}")
        # return self
