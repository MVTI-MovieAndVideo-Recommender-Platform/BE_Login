from typing import Annotated

from auth.jwt import verify_access_token
from database import mysql_conn
from fastapi import BackgroundTasks, Depends, Header
from routes.apihelper import base64_to_uuid
from routes.apihelper.delete_apihelpler import delete_mysql_and_messaging
from sqlalchemy.ext.asyncio import AsyncSession


async def delete_user(
    background_tasks: BackgroundTasks,
    jwt: Annotated[str, Header(convert_underscores=False)],
    mysql_db: AsyncSession = Depends(mysql_conn.get_db),
):
    user_id = base64_to_uuid(verify_access_token(jwt).get("token"))
    return await delete_mysql_and_messaging(user_id, background_tasks, mysql_db)
