from ninja import Field, Schema
from pydantic import ConfigDict


class CreateTagSchema(Schema):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    color: str = Field(default="#808080", pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color code validation
