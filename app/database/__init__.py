from database.connect import Settings, conn_kafka, conn_mongo, conn_mysql

# Settings 클래스를 인스턴스화 해서 .env 값을 가져온다.
settings = Settings()

# SQLAlchemy를 사용하는 경우
MYSQL_URL = f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PWD}@{settings.MYSQLDB_HOST}:{3306}/{settings.MYSQLDB_NAME}"
MONGODB_URL = f"mongodb://{settings.DB_USER}:{settings.DB_PWD}@{settings.MONGODB_HOST}:{27017}/?authSource={settings.DB_USER}"

mysql_conn = conn_mysql(MYSQL_URL)
mongo_conn = conn_mongo(MONGODB_URL)
kafka_conn = conn_kafka(settings.KAFKA_HOST)
