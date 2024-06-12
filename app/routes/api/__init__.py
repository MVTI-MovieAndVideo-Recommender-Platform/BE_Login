from fastapi.routing import APIRoute
from routes.api.create_api import social_login

post_route = APIRoute(path="/login", endpoint=social_login, methods=["POST"])
