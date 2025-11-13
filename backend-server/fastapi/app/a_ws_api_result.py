# -*- coding: utf-8 -*-
# 파일 이름: a_ws_api_result.py
# 역할: 레시피 JSON 입력 → WebSocket 테스트 실행 API

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import json
import asyncio
from app.a_ws_client_result import run_test_with_recipe_data  # 외부 WebSocket 테스트 함수

# 라우터 생성
router = APIRouter(prefix="/ws-test", tags=["WebSocket Test"])

# ==================== JSON POST 엔드포인트 ====================
@router.post("/run_ws_test_json")
async def run_ws_test_json(recipe_json: dict):
    """
    recipe_json: {
        "id": ...,
        "title": "...",
        "content": "...",
        ...
    }
    """
    try:
        # 백그라운드로 WebSocket 테스트 실행
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, run_test_with_recipe_data, recipe_json)
        return JSONResponse({
            "status": "started",
            "message": f"레시피 '{recipe_json.get('title', '')}' 테스트 실행 중"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# ==================== 파일 업로드 엔드포인트 ====================
@router.post("/run_ws_test_file")
async def run_ws_test_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        recipe_json = json.loads(contents)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, run_test_with_recipe_data, recipe_json)
        return JSONResponse({
            "status": "started",
            "message": f"레시피 '{recipe_json.get('title', '')}' 테스트 실행 중"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# ==================== 서버 실행 (별도 실행용) ====================
# 주의: 이 파일은 라우터로 사용되지만, 필요시 별도 서버로도 실행 가능합니다.
if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn
    app = FastAPI(title="WebSocket 레시피 테스트 API")
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8010, reload=False)
