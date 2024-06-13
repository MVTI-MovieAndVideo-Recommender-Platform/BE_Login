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


async def update_mysql_and_messaging(user_id: str, mbti: str, mysql_db: AsyncSession):
    mbti = mbti.upper()
    if not mbti_type.get(mbti, None):
        raise HTTPException(status_code=400, detail=f"mbti 유형에 맞는 문자열이 아닙니다.")
    # MongoDB에서 유저 확인
    result = await mongo_conn.member["user"].find_one({"_id": user_id, "is_delete": False})
    if result:
        result = (
            await mysql_db.execute(select(UserModel).filter_by(user_id=user_id))
        ).scalar_one_or_none()
        if result and result.mbti != mbti_type.get(mbti):
            print(result.mbti, mbti_type.get(mbti))
            result.mbti = mbti_type.get(mbti)
            await mysql_db.commit()
            print(f"Updated user_id {user_id} with new MBTI: {mbti_type.get(mbti)}")
        else:
            raise HTTPException(
                status_code=400, detail=f"동일 mbti이거나 Mysql에 데이터가 존재하지 않습니다"
            )
        update_time = (
            await mysql_db.execute(select(UserModel).filter_by(user_id=user_id))
        ).scalar_one_or_none()
        model = {
            "user_id": result.user_id,
            "mbti": mbti,
            "last_update": update_time.last_update.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        await produce_messages([message("update", "user", model)])
        return "mbti가 업데이트 되었습니다."
    else:
        raise HTTPException(status_code=400, detail=f"MongoDB에 데이터가 존재하지 않습니다")
