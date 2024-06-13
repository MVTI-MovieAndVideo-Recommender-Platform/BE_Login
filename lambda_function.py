from mangum import Mangum

from app.main import app

# Mangum 핸들러 생성
lambda_handler = Mangum(app)
