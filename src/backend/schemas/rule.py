from ninja import Schema
from pydantic import Field


class CreateRuleSchema(Schema):
    name: str = Field(..., max_length=255, json_schema_extra={"example": "Allow_HTTP"})
    description: str | None = Field(None, max_length=255, json_schema_extra={"example": "Allow HTTP traffic"})
    action: str = Field(..., max_length=255, json_schema_extra={"example": "accept"})
    log_type: str = Field(..., max_length=255, json_schema_extra={"example": "log"})
