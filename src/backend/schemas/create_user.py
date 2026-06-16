from ninja import Schema
from pydantic import Field


class CreateUserSchema(Schema):
    username: str = Field(..., example="alice")
    email: str = Field(..., example="alice@example.com")
    password: str = Field(..., example="password123")
