from database import settings
from jose import JWTError, jwt


# jwt 토큰을 생성하는 함수
def create_jwt(token: str, provider: str) -> str:
    payload = {"token": token, "provider": provider}
    try:
        return jwt.encode(payload, settings.SERVER_SECRET_KEY, algorithm="HS256")
    except JWTError:
        raise ValueError("인코딩이 되지 않았습니다.")


# jwt 토큰을 검증하는 함수 -> 디코드된 토큰을 반환한다
def verify_access_token(jwt_token: str) -> str:
    try:
        # 토큰을 decode한 값을 data에 저장한다.
        # 이 단계에서 decode되지 않으면 당연히 검증된 토큰이 아니다.
        return jwt.decode(jwt_token, settings.SERVER_SECRET_KEY, algorithms="HS256")
    except JWTError:
        raise ValueError("디코딩 이 불가합니다.")
