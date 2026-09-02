from ninja import Field, Schema


class CreateTagObjectSchema(Schema):
    object_type: str = Field(..., description="The type of the object to tag (e.g., 'Address', 'Service').")
    object_id: int = Field(..., description="The ID of the object to tag.")
    name: str = Field(..., description="The name of the tag.")
    description: str = Field("", description="A description for the tag.")
    color: str = Field("#808080", description="The color of the tag.")
