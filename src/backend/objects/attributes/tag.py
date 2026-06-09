

class Tag:
    def __init__(self, id: int, name:str, description:str, tenant_id: int):
        self.id = id
        self.name = name
        self.description = description
        self.tenant_id = tenant_id

    def __str__(self):
        return f"tag(id={self.id}, name={self.name}, description={self.description}, tenant_id={self.tenant_id})"