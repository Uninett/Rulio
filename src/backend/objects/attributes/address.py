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




# class ipv4Address:
#     """Defines an IPv4 address and validates it. Stores the address as a string and as a list of ints where each int is an octet."""
#     def __init__(self, address: str):
#         self.address = address
#         self.octets = self.address.split('.')
#         self.octets = [int(octet) for octet in self.octets] # Convert octets to integers
#         self.validate()
       

#     def validate(self):
#         """Checks that each octet is a number between 0 and 255, and that there are exactly 4 octets."""

#         if len(self.octets) != 4:
#             raise ValueError("Invalid IPv4 address format")
#         for octet in self.octets:
#             if not octet.isdigit() or not (0 <= int(octet) <= 255):
#                 raise ValueError("Invalid IPv4 address format")

#     def __str__(self):
#         return self.address