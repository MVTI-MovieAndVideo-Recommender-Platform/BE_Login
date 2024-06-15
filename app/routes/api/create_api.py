from typing import Annotated

from database import mysql_conn
from fastapi import BackgroundTasks, Depends, Header, HTTPException, Request, Response
from model.table import get_accesstoken
from routes.apihelper.create_apihelper import login_by_kakao, login_by_naver
from sqlalchemy.ext.asyncio import AsyncSession


async def social_login(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    mysql_db: AsyncSession = Depends(mysql_conn.get_db),
):
    req = get_accesstoken(
        request.headers.get("accesstoken"),
        request.headers.get("state"),
        request.headers.get("provider").lower(),
    )
    if req.provider == "kakao":
        result = await login_by_kakao(req, background_tasks, mysql_db)
        if type(result) == str:
            response.headers["jwt"] = result
    elif req.provider == "naver":
        result = await login_by_naver(req, background_tasks, mysql_db)
        if type(result) == str:
            response.headers["jwt"] = result
    else:
        raise HTTPException(status_code=400, detail="잘못된 로그인 방식입니다.")
    return {"status": "로그인에 성공하였습니다"}
