

class FilterInterface:
    def __init__(self, interface_id: int, filter_id: int, direction: str, sequence):
        self.interface_id = interface_id
        self.filter_id = filter_id
        self.direction = direction
        self.sequence = sequence

    def __str__(self):
        return f"FilterInterface(interface_id={self.interface_id}, filter_id={self.filter_id}, direction='{self.direction}', sequence={self.sequence})"