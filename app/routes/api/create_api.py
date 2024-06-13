from typing import Annotated

from database import mysql_conn
from fastapi import Depends, Header, HTTPException
from model.table import get_accesstoken
from routes.apihelper.create_apihelper import login_by_kakao, login_by_naver
from sqlalchemy.ext.asyncio import AsyncSession


# 소셜 로그인 함수
async def social_login(
    accesstoken: Annotated[str, Header(convert_underscores=False)] = None,
    state: Annotated[str | None, Header(convert_underscores=False)] = None,
    provider: Annotated[str, Header(convert_underscores=False)] = None,
    mysql_db: AsyncSession = Depends(mysql_conn.get_db),
):
    req = get_accesstoken(accesstoken, state, provider.lower())
    if req.provider == "kakao":
        return await login_by_kakao(req, mysql_db)
    elif req.provider == "naver":
        return await login_by_naver(req, mysql_db)
    else:
        raise HTTPException(status_code=400, detail="잘못된 로그인 방식입니다.")
