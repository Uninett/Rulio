from ninja import Schema
from pydantic import Field


class CreateUserSchema(Schema):
    username: str = Field(..., json_schema_extra={"example": "alice"})
    email: str = Field(..., json_schema_extra={"example": "alice@example.com"})
    password: str = Field(..., json_schema_extra={"example": "password123"})
    permissions: list[str] = Field(default=[], json_schema_extra={"example": ["member", "admin"]})
    tenant_id: int = Field(..., json_schema_extra={"example": 1})
