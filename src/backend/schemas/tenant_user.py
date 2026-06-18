from ninja import Schema
from pydantic import Field, ConfigDict


class CreateTenantUserSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(..., min_length=1, max_length=255, example="1")
    user_id: str = Field(..., min_length=1, max_length=255, example="1")
    role: str = Field(..., min_length=1, max_length=255, example="member")
