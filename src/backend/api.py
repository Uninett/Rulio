from ninja import NinjaAPI

from backend.services.create import create_address
from backend.objects import *

api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return "Hello world"

@api.get("/create_address")
def create_address(request, address: str):
    return create_address(address)

