from ninja import Schema
from pydantic import Field, ConfigDict


class CreateAddressGroupSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str
