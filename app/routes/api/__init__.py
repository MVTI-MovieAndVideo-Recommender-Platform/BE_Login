from fastapi.routing import APIRoute
from routes.api.create_api import social_login

post_route = APIRoute(path="/login", endpoint=social_login, methods=["POST"])

update_route = APIRoute(path="/editmbti", endpoint=update_mbti, methods=["PATCH"])
