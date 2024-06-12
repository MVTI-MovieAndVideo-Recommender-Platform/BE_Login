from typing import Optional

from model import Base
from pydantic import BaseModel
from sqlalchemy import CHAR, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


# User 테이블 CQRS : Create
class UserModel(Base):
    __tablename__ = "user"

    user_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    birthyear: Mapped[int] = mapped_column(Integer, nullable=False)
    mbti: Mapped[str] = mapped_column(CHAR(4), nullable=True)
    last_update: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    is_delete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    class Config:
        orm_mode = True

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# 인증 테이블 CQRS : Create
class AuthModel(Base):
    __tablename__ = "auth"

    token: Mapped[str] = mapped_column(CHAR(22), primary_key=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


# 로그인 인증 클래스
class AccessTokenRequest(BaseModel):
    accesstoken: str
    state: Optional[str] = None
    provider: str


def get_accesstoken(accesstoken: str, state: str, provider: str) -> AccessTokenRequest:
    return AccessTokenRequest(accesstoken=accesstoken, state=state, provider=provider)
