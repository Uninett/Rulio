from ninja import Schema
from pydantic import Field, model_validator, ConfigDict


class LoginSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=1, max_length=255, example="alice")
    password: str = Field(..., min_length=1, max_length=255, example="password123")
