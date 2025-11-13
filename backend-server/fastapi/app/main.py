# main.py
# python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
import os # [추가]
import sys # [추가]

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_LIBRARY", "serial")
os.environ.setdefault("KMP_BLOCKTIME", "0")
os.environ.setdefault("KMP_SETTINGS", "TRUE")
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
os.environ.setdefault("TORCH_NUM_THREADS", "1")
os.environ.setdefault("PYTORCH_ENABLE_MKLDNN", "0")
os.environ.setdefault("PYTHONNOUSERSITE", "1")

from dotenv import load_dotenv # <-- [수정] 1. 이 줄을 추가
load_dotenv() # <-- [수정] 2. 이 줄을 추가 (다른 import보다 먼저 실행)

# 1. 'fastapi' 폴더(프로젝트 루트)의 경로를 찾습니다.
# 이 파일(main.py)은 'app' 폴더 안에 있습니다.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# 'app' 폴더의 부모 폴더, 즉 'fastapi' 폴더
PROJECT_ROOT = os.path.dirname(APP_DIR)

# 2. .env 파일의 절대 경로를 지정합니다.
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# 3. .env 파일이 존재하는지 확인하고 로드합니다.
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
    print(f"✅ .env 파일 로드 성공: {DOTENV_PATH}")
else:
    print(f"🚨 [치명적 오류] .env 파일을 찾을 수 없습니다: {DOTENV_PATH}")
    # .env 파일이 없으면 서버를 실행할 수 없으므로 종료
    sys.exit(f"Error: .env file not found at {DOTENV_PATH}")

# 4. 'vision_task' 등 다른 폴더를 import할 수 있도록 경로 추가
# (이전 ModuleNotFoundError 방지)
sys.path.append(PROJECT_ROOT)

# 공용 캐시/설정 경로를 프로젝트 내부로 지정 (권한 문제 회피)
ULTRALYTICS_SETTINGS_ROOT = os.path.join(PROJECT_ROOT, ".ultralytics")
os.environ.setdefault("ULTRALYTICS_SETTINGS_DIR", ULTRALYTICS_SETTINGS_ROOT)
os.environ.setdefault("ULTRALYTICS_CACHE_DIR", os.path.join(ULTRALYTICS_SETTINGS_ROOT, "cache"))

HF_CACHE_ROOT = os.path.join(PROJECT_ROOT, ".cache", "huggingface")
os.environ.setdefault("HF_HOME", HF_CACHE_ROOT)
os.environ.setdefault("TRANSFORMERS_CACHE", HF_CACHE_ROOT)
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", HF_CACHE_ROOT)

for path in (
    ULTRALYTICS_SETTINGS_ROOT,
    os.environ["ULTRALYTICS_CACHE_DIR"],
    HF_CACHE_ROOT,
):
    os.makedirs(path, exist_ok=True)

# --- [수정된 부분 끝] ---

from fastapi import FastAPI
from app.api import router as api_router   # api.py의 router를 api_router라는 이름으로 임포트
from app.cook_api import router as cook_router  # cook_api.py의 router 추가
# 비전 관련 라우터 임포트
from app.a_vision_api import router as vision_router
from app.a_vision_pipeline import get_pipeline

from app.a_rag_api import router as rag_router # a_rag_api.py의 router 임포트
from app.a_ws_api_result import router as ws_test_router # a_ws_api_result.py의 router 임포트
# 1) 앱 생성
app = FastAPI(
    title="레시피 추천 API",
    description="사용자 재료 기반 레시피 추천 서비스",
    version="1.0.0"
)

# 2) 라우터 포함 — 반드시 app 선언 이후에!
#    prefix는 api.py에서 사용한 APIRouter(prefix="...")와 중복되지 않도록
app.include_router(api_router, prefix="/api/fastapi")
app.include_router(cook_router, prefix="/api/fastapi")
"""
    비전 테스크 API 추가 /detect 가 실제 사용할 API 나머지는 테스트용임
"""
app.include_router(vision_router, prefix="/api/fastapi/vision", tags=["Vision"])

# RAG LLM API 라우터 포함
app.include_router(rag_router, prefix="/api/fastapi/llm", tags=["RAG_LLM"])

# WebSocket 테스트 API 라우터 포함
app.include_router(ws_test_router, prefix="/api/fastapi", tags=["WebSocket Test"])

# 3) 헬스체크용 루트 엔드포인트
@app.get("/")
async def read_root():
    return {"message": "레시피 추천 API 서버가 실행 중입니다."}