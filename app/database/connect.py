from typing import Optional

from confluent_kafka import Producer
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# Setting config load
class Settings(BaseSettings):
    SERVER_SECRET_KEY: Optional[str] = None
    KAKAO_CLIENT_ID: Optional[str] = None
    KAKAO_RESTAPI_KEY: Optional[str] = None
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PWD: Optional[str] = None
    MYSQLDB_NAME: Optional[str] = None
    MYSQLDB_HOST: Optional[str] = None
    MONGODB_HOST: Optional[str] = None
    KAFKA_HOST: Optional[str] = None

    class Config:
        env_file = ".env"


# 데이터베이스 테이블 연결하는 클래스
class conn_mysql:
    def __init__(self, engine_url):
        self._engine = create_async_engine(engine_url, echo=False)
        self._async_sessionmaker = async_sessionmaker(bind=self._engine, expire_on_commit=False)

        # 데이터베이스 연결 시 타임존 설정 이벤트 리스너 추가
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_timezone(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("SET time_zone = 'Asia/Seoul'")
            cursor.close()

    async def init_db(self):
        async with self._engine.begin() as conn:
            print("mysql 연결 되었습니다.")
            await conn.run_sync(lambda conn: None)

    async def get_session(self) -> AsyncSession:  # type: ignore
        async with self._async_sessionmaker() as session:
            yield session

    async def get_db(self) -> AsyncSession:  # type: ignore
        async for session in self.get_session():
            yield session


def conn_mongo(engine_url) -> AsyncIOMotorClient:
    print("MongoDB 연결 되었습니다.")
    return AsyncIOMotorClient(engine_url)


def conn_kafka(server):
    return Producer(**{"bootstrap.servers": server})
