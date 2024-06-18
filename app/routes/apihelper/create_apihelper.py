import json
import uuid

import httpx
from auth.jwt import create_jwt
from database import settings
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse
from model.table import AuthModel, UserModel
from routes.apihelper import message, model_to_dict, produce_messages, uuid_to_base64
from routes.apihelper.read_apihelper import user_auth_collection_check
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# 카카오 로그인 함수 구현 CQRS : Create
async def login_by_kakao(
    access_token: str, background_tasks: BackgroundTasks, mysql_db: AsyncSession
):
    print("this is login_by_kakao api")
    # response = await kakao_auth_token(code)
    # if not response:
    #     raise HTTPException(status_code=400, detail="access_token이 생성이 안됩니다.")
    response = await kakao_get_data(access_token)
    if not response:
        raise HTTPException(status_code=400, detail="response가 반환이 안됩니다.")
    user, auth = make_user_data(response, "kakao")
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
    code: str, state: str, background_tasks: BackgroundTasks, mysql_db: AsyncSession
):
    print("this is login_by_naver api")
    response = await naver_auth_token(code, state)
    if not response:
        raise HTTPException(status_code=400, detail="access_token이 생성이 안됩니다.")
    response = await naver_get_data(response)
    if not response:
        raise HTTPException(status_code=400, detail="response가 반환이 안됩니다.")
    user, auth = make_user_data(response, "naver")
    res = await user_auth_collection_check(user.user_id, user.email, auth.provider)
    if type(res) == bool and res:
        await insert_db_and_kafka_message(user, auth, background_tasks, mysql_db)
        return create_jwt(token=auth.token, provider=auth.provider)  # jwt 토큰 반환
    elif type(res) == str:  # 유저가 있으니 create_jwt 생성해서 반환
        return res
    else:
        raise HTTPException(status_code=400, detail=str(res))


# 카카오 엑세스코드 발급
# async def kakao_auth_token(code: str):
#     async with httpx.AsyncClient() as client:
#         token_response = await client.post(
#             "https://kauth.kakao.com/oauth/token",
#             data={
#                 "grant_type": "authorization_code",
#                 "client_id": settings.KAKAO_CLIENT_ID,
#                 "redirect_uri": "http://localhost:8000/member/login/kakao/callback",
#                 "code": code,
#                 "client_secret": settings.KAKAO_RESTAPI_KEY,
#             },
#             headers={"Content-Type": "application/x-www-form-urlencoded"},
#         )
#     token_response.raise_for_status()
#     return token_response.json().get("access_token", None)


# 카카오 유저 데이터 발급 함수
async def kakao_get_data(access_token: str) -> dict:
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer ${access_token}",
    }
    async with httpx.AsyncClient(http2=True) as client:
        return json.loads((await client.get(url, headers=headers)).text)


# 네이버 access_token 발급 함수
async def naver_auth_token(code, state) -> str:
    token_url = f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id={settings.NAVER_CLIENT_ID}&client_secret={settings.NAVER_CLIENT_SECRET}&code={code}&state={state}"
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.get(token_url)
        response.raise_for_status()
        return json.loads(response.text).get("access_token")


# 네이버 유저 데이터 발급 함수
async def naver_get_data(access_token: str) -> dict:
    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(http2=True) as client:
        return json.loads((await client.get(url, headers=headers)).text)


# 응답 받은 유저 정보를 db에 넘기기 위한 모델로 변환하는 함수
def make_user_data(response: dict, provider: str) -> (UserModel, AuthModel):  # type: ignore
    print("리스폰스 : ", response)

    if provider == "kakao":
        response = response.get("kakao_account")
        user_gender = "M" if response.get("gender") == "male" else "F"
    elif provider == "naver":
        response = response.get("response")
        user_gender = response.get("gender")
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
    print(user_result)
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

    return model_to_dict(user_result), model_to_dict(auth_result)
