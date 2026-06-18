from ninja import Schema, Field
from pydantic import ConfigDict


class CreateTagSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str
