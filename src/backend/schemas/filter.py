from ninja import Schema
from pydantic import Field


class CreateFilterSchema(Schema):
    name: str = Field(..., max_length=255, example="Filter Name")
    description: str
