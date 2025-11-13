import os
import logging
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from app.api import router as api_router
from app.cook_api import router as cook_router
from app.vision_api import router as vision_router
from app.vision_pipeline import get_pipeline

logging.basicConfig(level=logging.INFO)
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행될 로직"""
    logging.info("  서버 시작: 비전 파이프라인 로딩 중...")
    await asyncio.to_thread(get_pipeline)
    logging.info("  비전 파이프라인 로딩 완료!")

    yield
    
    logging.info("  서버 종료")

app = FastAPI(
    title="레시피 추천 API",
    description="사용자 재료 기반 레시피 추천 서비스",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/fastapi")
app.include_router(cook_router, prefix="/api/fastapi")
app.include_router(vision_router, prefix="/api/fastapi/vision", tags=["Vision"])

@app.get("/")
async def read_root():
    return {"message": "레시피 추천 API 서버가 실행 중입니다."}

# macOS에서 안전한 실행 설정
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # reload 비활성화 - macOS multiprocessing 충돌 방지
        workers=1,
        loop="asyncio",
        log_level="info"
    )