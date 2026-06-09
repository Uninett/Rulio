from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return "Hello world"

# @api.get("/create_address")
# def create_address(request):
#     from .services import create_address
#     return create_address()