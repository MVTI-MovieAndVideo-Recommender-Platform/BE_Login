from typing import Annotated

from auth.jwt import verify_access_token
from database import mysql_conn
from fastapi import Depends, Header
from routes.apihelper import base64_to_uuid
from routes.apihelper.update_apihelpler import update_mysql_and_messaging
from sqlalchemy.ext.asyncio import AsyncSession


async def update_mbti(
    jwt: Annotated[str, Header(convert_underscores=False)] = None,
    mbti: str = None,
    mysql_db: AsyncSession = Depends(mysql_conn.get_db),
):
    user_id = base64_to_uuid(verify_access_token(jwt).get("token"))
    return await update_mysql_and_messaging(user_id, mbti, mysql_db)
