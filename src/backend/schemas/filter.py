from ninja import Schema
from pydantic import Field


class CreateFilterSchema(Schema):
    name: str = Field(..., max_length=255, json_schema_extra={"example": "Filter Name"})
    description: str
