from fastapi import APIRouter
from routes.api import (
    delete_route,
    get_kakao_redirect_route,
    kakao_login_route,
    naver_login_route,
    update_route,
)

login_router = APIRouter(tags=["Login"])

login_router.routes.append(kakao_login_route)
login_router.routes.append(naver_login_route)
login_router.routes.append(get_kakao_redirect_route)
login_router.routes.append(update_route)
login_router.routes.append(delete_route)
