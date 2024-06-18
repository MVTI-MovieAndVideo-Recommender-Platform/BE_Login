from contextlib import asynccontextmanager

from database import mysql_conn
from fastapi import FastAPI, Request, Response, requests
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from routes import login_router
from sqlalchemy.ext.asyncio import close_all_sessions
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mysql_conn.init_db()
    yield
    await close_all_sessions()


app = FastAPI(lifespan=lifespan, root_path="/member")
# 세션 미들웨어 추가 (비밀키는 실제 환경에서 안전하게 관리)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "PATCH", "DELETE"],  # 허용할 HTTP 메서드
    allow_headers=["access_token", "state", "code", "provider", "jwt"],  # 허용할 HTTPS 헤더
    expose_headers=["jwt"],
)

app.include_router(login_router, prefix="")


# 예외 처리
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print(f"OMG! An HTTP error!: {repr(exc)}")
    return await http_exception_handler(request, exc)


# 예외 처리
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"OMG! The client sent invalid data!: {exc}")
    return await request_validation_exception_handler(request, exc)


@app.get("/")
async def read_root():
    return {"message": "Welcome to Login API_SERVER with FastAPI"}


@app.get("/healthcheck")
async def get_healthcheck():
    return {"status": "OK"}
