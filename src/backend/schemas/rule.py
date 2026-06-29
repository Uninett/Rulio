from ninja import Schema
from pydantic import Field


class CreateRuleSchema(Schema):
    name: str = Field(..., max_length=255, example="Allow_HTTP")
    description: str | None = Field(None, max_length=255, example="Allow HTTP traffic")
    action: str = Field(..., max_length=255, example="accept")
    log_type: str = Field(..., max_length=255, example="log")
    enable: bool = Field(default=True, example=True)
