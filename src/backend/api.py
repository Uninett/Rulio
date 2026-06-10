from django.contrib.auth.models import User

from ninja import NinjaAPI


api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return "Hello world"

@api.get("/members")
def members(request):
    return list(User.objects.values())

@api.post("/create_user")
def create_user(request, username: str, email: str, password: str):
    if User.objects.filter(username=username).exists():
        return {"status": "error", "message": f"User with username '{username}' already exists."}
    
    user = User.objects.create_user(username=username, email=email, password=password)
    return {"status": "success", "message": f"User '{username}' created successfully.", "user_id": user.id}

@api.delete("/delete_user")
def delete_user(request, user_id: int):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return {"status": "success", "message": f"User with id {user_id} deleted."}
    except User.DoesNotExist:
        return {"status": "error", "message": f"User with id {user_id} does not exist."}

# @api.get("/create_address")
# def create_address(request):
#     from .services import create_address
#     return create_address()