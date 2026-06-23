from ninja import Schema
from pydantic import Field, model_validator, ConfigDict


class CreateRuleSchema(Schema):
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=255)
    action: str = Field(..., max_length=255)
    log_type: str = Field(..., max_length=255)
    enable: bool = Field(default=True)
