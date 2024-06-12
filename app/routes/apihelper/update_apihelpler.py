from database import mongo_conn
from fastapi import BackgroundTasks, HTTPException
from model.table import UserModel
from routes.apihelper import message, produce_messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

mbti_type = {
    "ISTP": "ISTP",
    "ISFP": "ISFP",
    "INFP": "INFP",
    "INTP": "INTP",
    "ESTP": "ESTP",
    "ESFP": "ESFP",
    "ENFP": "ENFP",
    "ENTP": "ENTP",
    "ISTJ": "ISTJ",
    "ISFJ": "ISFJ",
    "INFJ": "INFJ",
    "INTJ": "INTJ",
    "ESTJ": "ESTJ",
    "ESFJ": "ESFJ",
    "ENFJ": "ENFJ",
    "ENTJ": "ENTJ",
}


async def update_mysql_and_messaging(
    user_id: str, mbti: str, background_tasks: BackgroundTasks, mysql_db: AsyncSession
):
    if not mbti_type.get(mbti.upper(), None):
        raise HTTPException(status_code=400, detail=f"mbti 유형에 맞는 문자열이 아닙니다.")
    # MongoDB에서 유저 확인
    result = await mongo_conn.member["user"].find_one({"_id": user_id, "is_delete": False})
    if result:
        async with mysql_db as session:
            try:
                result = (
                    await session.execute(select(UserModel).filter_by(user_id=user_id))
                ).scalar_one_or_none()
                if result:
                    result.mbti = mbti_type.get(mbti.upper())
                    await session.commit()
                    print(f"Updated user_id {user_id} with new MBTI: {mbti_type.get(mbti.upper())}")
                update_time = (
                    await session.execute(select(UserModel).filter_by(user_id=user_id))
                ).scalar_one_or_none()
                model = {
                    "user_id": result.user_id,
                    "mbti": mbti,
                    "last_update": update_time.last_update.strftime("%Y-%m-%dT%H:%M:%S"),
                }
                background_tasks.add_task(produce_messages, [message("update", "user", model)])
                return "mbti가 업데이트 되었습니다."
            except:
                raise HTTPException(status_code=400, detail=f"Mysql에 데이터가 존재하지 않습니다")
            finally:
                await session.close()
    else:
        raise HTTPException(status_code=400, detail=f"MongoDB에 데이터가 존재하지 않습니다")
