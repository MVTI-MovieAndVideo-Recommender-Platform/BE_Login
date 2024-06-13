from database import mongo_conn
from model.table import UserModel
from routes.apihelper import message, produce_messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def delete_mysql_and_messaging(user_id: str, mysql_db: AsyncSession):
    # MongoDB에서 유저 확인
    result = await mongo_conn.member["user"].find_one({"_id": user_id, "is_delete": False})
    if result:
        async with mysql_db as session:
            async with session.begin():
                query = select(UserModel).filter_by(user_id=user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user and not user.is_delete:
                    user.is_delete = True
                    model = {"user_id": user.user_id, "is_delete": True}
                    user_name = user.name
                    await session.commit()
                    print(f"Updated user_id {user_id} is delete")
                    await produce_messages([message("delete", "user", model)])
                    return f"{user_name}님은 정상적으로 탈퇴 되었습니다."
                else:
                    print(f"User with user_id {user_id} not found in MySQL")
    else:
        print(f"User with user_id {user_id} not found in MongoDB")
