

class TagObject:
    def __init__(self, tag_id: int, object_type: str, object_id: int, tennant_id: int):
        self.tag_id = tag_id
        self.object_type = object_type
        self.object_id = object_id
        self.tennant_id = tennant_id

    def __str__(self):
        return f"tag_object(tag_id={self.tag_id}, object_type='{self.object_type}', object_id={self.object_id}, tennant_id={self.tennant_id})"