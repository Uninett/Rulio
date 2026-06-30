from ninja import Schema
from pydantic import Field


class CreateDeviceSchema(Schema):
    name: str = Field(..., max_length=255, json_schema_extra={"example": "Device Name"})
    description: str
    platform: str = Field(..., max_length=255, json_schema_extra={"example": "juniper"})
    type: str = Field(..., max_length=255, json_schema_extra={"example": "firewall"})
