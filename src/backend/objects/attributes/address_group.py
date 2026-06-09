

class AddressGroup:
    def __init__(self, id: int, tenant_id: int, name: str, description: str):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        
    def __str__(self):
        return f"AddressGroup(id={self.id}, tenant_id={self.tenant_id}, name='{self.name}', description='{self.description}')" 