# 파일 이름: main_api_pjh.py
# 위치: /Users/server/Desktop/cookduck_backup/backend-server/fastapi/fastapi_gateapi/
# 역할: 'Vision API'만 로드하여 실행하는 메인 게이트웨이

import uvicorn
import os
import sys

# --- (중요) Python 경로 설정 ---
# 이 파일(main_api_pjh.py)이 'app' 폴더의 형제(sibling) 폴더에 있으므로,
# 'app' 폴더를 찾을 수 있도록 부모 폴더(fastapi)의 경로를 추가합니다.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'fastapi_gateapi'의 부모, 즉 'fastapi' 폴더
sys.path.append(PROJECT_ROOT) # 

from dotenv import load_dotenv

# --- (중요) .env 파일 로드 ---
# .env 파일은 'fastapi' 폴더(PROJECT_ROOT)에 있다고 가정합니다.
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ .env 파일 로드 성공: {dotenv_path}")
else:
    print(f"🚨 [경고] .env 파일을 찾을 수 없습니다: {dotenv_path}")
    print("YOLO/VLM 모델 경로가 환경 변수에 수동으로 설정되어 있어야 합니다.")

from fastapi import FastAPI
# [수정] 'app' 폴더에서 'vision_api' 라우터만 임포트합니다.
from app.vision_api import router as vision_router

# (참고: vision_pipeline은 vision_api가 내부적으로 임포트하므로 여기서 직접 호출할 필요가 없습니다.)
# from app.vision_pipeline import get_pipeline # <--- 이 줄은 main에서 직접 사용하지 않으면 불필요

# 1) 앱 생성
app = FastAPI(
    title="Vision API 서버 (단독 실행)",
    description="식재료 이미지 인식을 위한 API 서버",
    version="1.0.0",
    docs_url="/docs" # Swagger UI 활성화
)

# 2) [수정] 'vision_router'만 포함
app.include_router(vision_router, prefix="/api/fastapi/vision", tags=["Vision"])

# 3) 헬스체크용 루트 엔드포인트
@app.get("/")
async def read_root():
    return {"message": "Vision API 서버가 실행 중입니다."}

# 4) (수정) uvicorn 서버를 직접 실행하기 위한 코드 추가
if __name__ == "__main__":
    print("--- Vision API 서버(main_api_pjh.py)를 8000 포트로 시작합니다 ---")
    # (참고: uvicorn app.main:app 대신 python main_api_pjh.py로 실행 가능)
    uvicorn.run(app, host="0.0.0.0", port=8000)