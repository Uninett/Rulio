from ninja import Schema, Field
from pydantic import ConfigDict


class CreateTagObjectSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    tag_id: int = Field(..., ge=1)
    object_type: str = Field(..., min_length=1, max_length=255)
    object_id: int = Field(..., ge=1)
