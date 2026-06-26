
from ninja import Schema
from pydantic import Field


class CreateInterfaceSchema(Schema):
    name: str = Field(..., max_length=255, example="eth0")
    description: str
    device_id: int = Field(..., example=1)
    type: str = Field(..., max_length=255, example="ethernet")

