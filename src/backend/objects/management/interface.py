

class Interface:
    def __init__(self, id: int, device_id: int, name: str, type: str, VRF: str, description: str):
        self.id = id
        self.device_id = device_id
        self.name = name
        self.type = type
        self.VRF = VRF
        self.description = description

    def __str__(self):
        return f"Interface(id={self.id}, device_id={self.device_id}, name='{self.name}', type='{self.type}', VRF='{self.VRF}', description='{self.description}')"