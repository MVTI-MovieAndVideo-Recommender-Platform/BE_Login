from fastapi import  FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # 허용할 HTTP 메서드
    allow_headers=["*"],  # 허용할 HTTP 헤더
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to Login API_SERVER with FastAPI"}

@app.get("/healthcheck")
async def get_healthcheck():
    return {"status":"OK"}