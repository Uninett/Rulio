

class Filter:
    def __init__(self, id: int, name: str, description: str, tennant_id: int, enable: bool):
        self.id = id
        self.name = name
        self.description = description
        self.tennant_id = tennant_id
        self.enable = enable

    def __str__(self):
        return f"filter(id={self.id}, name='{self.name}', description='{self.description}', tennant_id={self.tennant_id}, enable={self.enable})"