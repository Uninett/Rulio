import ipaddress

class Address:
    def __init__(self, id: int, name: str, description: str, tenant_id: int, type: str, ipv4_value: ipaddress.IPv4Address, ipv6_value: ipaddress.IPv6Address):
        self.id = id
        self.name = name
        self.description = description
        self.tenant_id = tenant_id
        self.type = type
        self.ipv4_value = ipv4_value
        self.ipv6_value = ipv6_value



    def __str__(self):
        return f"Address(id={self.id}, name='{self.name}', description='{self.description}', tenant_id={self.tenant_id}, type='{self.type}', ipv4_value='{self.ipv4_value}', ipv6_value='{self.ipv6_value}')"




