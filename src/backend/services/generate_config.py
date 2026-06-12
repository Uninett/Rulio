

from aerleon.lib import naming  
from aerleon import api as aerleon_api

from backend.objects.attributes.address import Address
from backend.objects.attributes.address_group import AddressGroup
from backend.objects.attributes.service import Service
from backend.objects.attributes.service_group import ServiceGroup

class Policy:
    """
    A class for the input to aerleons Generate function. 
    This class will take in a list of rules and convert them into the format that aerleon expects. 
    The rules will be in the form of our internal data models (Address, Service, AddressGroup, ServiceGroup)
    and this class will convert them into the format that aerleon expects.

    Args:
        name (str): The name of the policy.
        rules (list[Object]): A list of rules in the form of our internal data models (Address, Service, AddressGroup, ServiceGroup).
        vendor (str): The name of the vendor for which to generate the configuration.
        type (str): The type of policy to generate (e.g. "acl", "nat", etc.).
    """
    def __init__(self, name: str, rules: list, vendor: str, type: str):
        self.name = name
        self.YAMLConfig = {}
        self.YAMLConfig["header"] = []
        self.YAMLConfig["terms"] = []
        for rule in rules:
            match rule:
                case rule.isinstance_of(Address):
                    self.add_address(**rule)
                case rule.isinstance_of(Service):
                    self.add_service(**rule)
                case rule.isinstance_of(AddressGroup):
                    self.add_address_group(**rule)
                case _:
                    raise ValueError(f"Unsupported rule type: {type(rule)}")

    def add_address(self, address: Address):
        pass

    def add_service(self, service: Service):
        pass

    def add_address_group(self, address_group: AddressGroup):
        pass

    def add_service_group(self, service_group: ServiceGroup):
        pass
        

def generate_config(policy: Policy, vendor: str) -> str:
    """
    Generates a configuration for the specified vendor based on the provided YAML configuration.

    Args:
        policy (Policy): The policy object containing the rules and configuration to be converted.
        vendor (str): The name of the vendor for which to generate the configuration.

    Returns:
        str: The generated configuration as a string.
    """
    definitions = naming.Naming()
    configs = aerleon_api.Generate([policy], definitions)
        
    acl = configs["cisco_example_policy.acl"]
        
    return acl