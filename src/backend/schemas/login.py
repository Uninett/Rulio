from ninja import Schema
from pydantic import Field, ConfigDict


class LoginSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "alice"})
    password: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "password123"})
