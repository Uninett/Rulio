from ninja import Schema


class MessageSchema(Schema):
    status: str
    message: str
