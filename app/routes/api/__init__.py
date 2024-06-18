from fastapi.routing import APIRoute
from routes.api.create_api import kakao_callback, kakao_login, naver_login
from routes.api.delete_api import delete_user
from routes.api.update_api import update_mbti

kakao_login_route = APIRoute(path="/login/kakao", endpoint=kakao_login, methods=["POST"])
naver_login_route = APIRoute(path="/login/naver", endpoint=naver_login, methods=["POST"])
get_kakao_redirect_route = APIRoute(
    path="/login/kakao/callback", endpoint=kakao_callback, methods=["GET"]
)
update_route = APIRoute(path="/editmbti", endpoint=update_mbti, methods=["PATCH"])

delete_route = APIRoute(path="/secession", endpoint=delete_user, methods=["delete"])
