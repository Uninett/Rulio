from ninja import Schema
from pydantic import Field


class CreateDeviceSchema(Schema):
    name: str = Field(..., max_length=255, example="Device Name")
    description: str
    platform: str = Field(..., max_length=255, example="juniper")
    type: str = Field(..., max_length=255, example="firewall")
