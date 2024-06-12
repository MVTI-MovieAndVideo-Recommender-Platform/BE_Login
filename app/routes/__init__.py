from fastapi import APIRouter
from routes.api import delete_route, post_route, update_route

login_router = APIRouter(tags=["Login"])

login_router.routes.append(post_route)
login_router.routes.append(update_route)
login_router.routes.append(delete_route)
