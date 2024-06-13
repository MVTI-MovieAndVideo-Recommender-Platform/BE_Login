import json
import uuid

import httpx
from auth.jwt import create_jwt
from database import settings
from fastapi import BackgroundTasks, HTTPException
from model.table import AuthModel, UserModel, get_accesstoken
from routes.apihelper import message, produce_messages, uuid_to_base64
from routes.apihelper.read_apihelper import user_auth_collection_check
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# 카카오 로그인 함수 구현 CQRS : Create
async def login_by_kakao(
    req: get_accesstoken,
    background_tasks: BackgroundTasks,
    mysql_db: AsyncSession,
):
    print("this is login_by_kakao api")
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer ${req.accesstoken}",
    }
    async with httpx.AsyncClient(http2=True) as client:
        response = json.loads((await client.post(url, headers=headers)).text)
        if not response:
            raise HTTPException(status_code=400, detail="정보가 없습니다.")
        user, auth = make_user_data(response, req.provider)
        res = await user_auth_collection_check(user.user_id, user.email, auth.provider)
        if type(res) == bool and res:
            await insert_db_and_kafka_message(user, auth, background_tasks, mysql_db)
            return create_jwt(token=auth.token, provider=auth.provider)  # jwt 토큰 반환
        elif type(res) == str:  # 유저가 있으니 create_jwt 생성해서 반환
            return res
        else:
            raise HTTPException(status_code=400, detail=str(res))


# 네이버 로그인 함수 구현 CQRS : Create
async def login_by_naver(
    req: get_accesstoken,
    background_tasks: BackgroundTasks,
    mysql_db: AsyncSession,
):
    print("this is login_by_naver api")
    accesstoken = await naver_auth_token(req)
    if not accesstoken:
        raise HTTPException(status_code=400, detail="accesstoken이 반환이 안됩니다.")
    response = await naver_get_data(accesstoken)
    if not response:
        raise HTTPException(status_code=400, detail="response가 반환이 안됩니다.")
    user, auth = make_user_data(response, req.provider)
    res = await user_auth_collection_check(user.user_id, user.email, auth.provider)
    if type(res) == bool and res:
        await insert_db_and_kafka_message(user, auth, background_tasks, mysql_db)
        return create_jwt(token=auth.token, provider=auth.provider)  # jwt 토큰 반환
    elif type(res) == str:  # 유저가 있으니 create_jwt 생성해서 반환
        return res
    else:
        raise HTTPException(status_code=400, detail=str(res))


# 네이버 access_token 발급 함수
async def naver_auth_token(req: get_accesstoken) -> str:
    token_url = f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id={settings.NAVER_CLIENT_ID}&client_secret={settings.NAVER_CLIENT_SECRET}&code={req.accesstoken}&state={req.state}"
    async with httpx.AsyncClient(http2=True) as client:
        response = json.loads((await client.get(token_url)).text)
        return response.get("access_token")


# 네이버 유저 데이터 발급 함수
async def naver_get_data(accesstoken: str) -> dict:
    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {accesstoken}"}
    async with httpx.AsyncClient(http2=True) as client:
        return json.loads((await client.get(url, headers=headers)).text)


# 응답 받은 유저 정보를 db에 넘기기 위한 모델로 변환하는 함수
def make_user_data(response: dict, provider: str) -> (UserModel, AuthModel):  # type: ignore
    print("리스폰스 : ", response)
    if provider == "kakao":
        response = response.get("kakao_account")
        user_gender = "M" if response.get("gender") == "male" else "F"
    elif provider == "naver":
        response, user_gender = response.get("response", ""), response.get("gender", "")
    user_id = uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=response.get("email")).__str__()

    user_data = UserModel(
        user_id=user_id,
        name=response.get("name"),
        email=response.get("email"),
        gender=user_gender,
        birthyear=int(response.get("birthyear")),
    )
    auth_data = AuthModel(token=uuid_to_base64(uuid.UUID(user_id)), provider=provider)
    return user_data, auth_data


# mysql에 데이터 입력하고 카프카에 메시지 보내는 함수
async def insert_db_and_kafka_message(
    user: UserModel,
    auth: AuthModel,
    background_tasks: BackgroundTasks,
    mysql_db: AsyncSession,
):
    mysql_db.add_all([auth, user])
    await mysql_db.commit()
    user_result, auth_result = await get_user_and_auth(user.user_id, auth.token, mysql_db)
    if user_result and auth_result:
        messages = [message("insert", "user", user_result), message("insert", "auth", auth_result)]
        background_tasks.add_task(produce_messages, messages)


async def get_user_and_auth(user_id: str, token: str, mysql_db: AsyncSession):
    user_id2base64 = uuid_to_base64(uuid.UUID(user_id))
    query = (
        select(UserModel, AuthModel)
        .join(AuthModel, user_id2base64 == AuthModel.token)
        .where(UserModel.user_id == user_id)
        .where(AuthModel.token == token)
    )
    result = await mysql_db.execute(query)
    user_result, auth_result = result.first()  # Assuming there's one matching record
    print(user_result, auth_result)

    return user_result, auth_result
