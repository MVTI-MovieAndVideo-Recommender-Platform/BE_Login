from typing import Annotated, Optional

import httpx
from database import mysql_conn, settings
from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from routes.apihelper.create_apihelper import login_by_kakao, login_by_naver
from sqlalchemy.ext.asyncio import AsyncSession


async def kakao_login(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    mysql_db: AsyncSession = Depends(mysql_conn.get_db),
):
    print("ACCESS_TOKEN", request.headers.get("access_token"))
    result = await login_by_kakao(request.headers.get("access_token"), background_tasks, mysql_db)
    if type(result) == str:
        response.headers["jwt"] = result
    else:
        raise HTTPException(status_code=400, detail="로그인 하는중에 오류가 발생하였습니다.")
    print(response.headers.get("jwt"))
    return {"status": "로그인에 성공하였습니다"}


async def naver_login(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    mysql_db: AsyncSession = Depends(mysql_conn.get_db),
):
    result = await login_by_naver(
        request.headers.get("code"), request.headers.get("state"), background_tasks, mysql_db
    )
    if type(result) == str:
        response.headers["jwt"] = result
    else:
        raise HTTPException(status_code=400, detail="로그인 하는중에 오류가 발생하였습니다.")
    print(response.headers.get("jwt"))
    return {"status": "로그인에 성공하였습니다"}


# 인가 코드 및 액세스코드 리다이렉션
async def kakao_callback(code: str, request: Request):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "redirect_uri": "https://api.mvti.site/member/login/kakao/callback",
                "code": code,
                "client_secret": settings.KAKAO_RESTAPI_KEY,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    token_response.raise_for_status()
    print("access_token : ", token_response.json().get("access_token", None))
    request.session["access_token"] = token_response.json().get("access_token", None)
    print(
        "리디렉션 할 uri ",
        f"https://mvti.site/login/kakao/callback?access_token={token_response.json().get('access_token', None)}",
    )

    return RedirectResponse(
        url=f"http://localhost:3000/login/kakao/callback?access_token={token_response.json().get('access_token', None)}"
    )
