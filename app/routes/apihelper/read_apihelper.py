import uuid

from auth.jwt import create_jwt
from database import mongo_conn
from routes.apihelper import uuid_to_base64


# db에 유저 데이터가있는지 확인하고 없으면 데이터 추가
async def user_auth_collection_check(
    user_id: str, email: str, provider: str
) -> str | bool | ValueError:
    # 로그인 유저가 DB에 있는지 검사한뒤
    if await email_verify_collection(email):
        print("유저 있음", flush=True)
        result = await token_verify_collection(user_id, provider)
        print("user_auth_collection_check : ", result)
        return result if type(result) == str else result
    else:
        print("유저 없음 회원가입 가능", flush=True)
        return True


# user collection에 데이터가 존재하는지 확인
async def email_verify_collection(email: str) -> bool:
    return True if await mongo_conn.member["user"].find_one({"email": email}) else False


# auth collection에 데이터가 있는지 확인하고
# 소셜 로그인 provider와 일치하는지 확인하는 함수
# jwt 토큰 반환
async def token_verify_collection(user_id: str, provider: str) -> str | ValueError:
    auth_collection_check = await read_auth_collection(user_id)
    if auth_collection_check and auth_collection_check.get("provider") == provider:
        return create_jwt(auth_collection_check.get("_id"), auth_collection_check.get("provider"))
    elif auth_collection_check.get("provider") != provider:
        return ValueError(auth_collection_check.get("provider") + " 로 가입된 계정이 있습니다.")
    else:
        return ValueError("잘못된 토큰값이 전달됨")


async def read_auth_collection(user_id: str) -> dict | None:
    return await mongo_conn.member["auth"].find_one({"_id": uuid_to_base64(uuid.UUID(user_id))})
