from typing import Optional

from ninja import Schema
from pydantic import Field


class CreateInterfaceSchema(Schema):
    name: str = Field(..., max_length=255, json_schema_extra={"example": "eth0"})
    description: str
    device_id: int = Field(..., json_schema_extra={"example": 1})
    type: Optional[str] = Field(None, max_length=255, json_schema_extra={"example": "ethernet"})
    VRF: Optional[str] = Field(None, max_length=255, json_schema_extra={"example": "VRF1"})
