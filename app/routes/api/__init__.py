from fastapi.routing import APIRoute
from routes.api.create_api import social_login
from routes.api.delete_api import delete_user
from routes.api.update_api import update_mbti

post_route = APIRoute(path="/login", endpoint=social_login, methods=["POST"])

update_route = APIRoute(path="/editmbti", endpoint=update_mbti, methods=["PATCH"])

delete_route = APIRoute(path="/secession", endpoint=delete_user, methods=["delete"])
