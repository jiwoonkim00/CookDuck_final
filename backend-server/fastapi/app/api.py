from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from app.faiss_search import recommend_recipes
from app.faiss_search_weighted import recommend_recipes_weighted
from app.faiss_search_new import recommend_recipes_new_table
import time
import httpx
import os
import uuid
import logging
import asyncio
import json

# 라우터 생성 및 CORS 설정
router = APIRouter()

# 추천 요청 모델
class RecommendRequest(BaseModel):
    ingredients: List[str]
    main_ingredients: List[str] = None  # 주재료 (옵션)
    sub_ingredients: List[str] = None   # 부재료 (옵션)
    main_weight: float = 2.0           # 주재료 가중치 (기본 2.0)

# 공통 RAG 처리 함수
async def apply_rag_if_enabled(
    results: List[dict],
    user_ingredients: List[str],
    use_rag: bool
) -> List[dict]:
    """
    RAG 옵션이 활성화된 경우 LLM으로 추천 문구 생성
    
    Args:
        results: FAISS로 검색된 레시피 목록
        user_ingredients: 사용자 보유 재료
        use_rag: RAG 활성화 여부
    
    Returns:
        RAG 처리된 레시피 목록 (실패 시 원본 반환)
    """
    if not use_rag or not results:
        return results
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        from .faiss_rag_service import enhance_recipes_with_llm
        
        # RAG 처리는 상위 20개 레시피만 처리 (성능 및 안정성 고려)
        enhanced_results = await enhance_recipes_with_llm(
            recipes=results,
            user_ingredients=user_ingredients,
            top_n=20  # 상위 20개 레시피만 LLM 처리
        )
        logger.info(f"RAG로 {len([r for r in enhanced_results if r.get('enhanced')])}개 레시피 설명 생성 완료")
        return enhanced_results
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"RAG 처리 실패, 원본 결과 반환: {e}")
        # RAG 실패 시 원본 결과 반환
        return results

# /recommend 엔드포인트 (recipe_new 테이블 사용 - 가중치 기반 추천)
@router.post("/recommend", response_model=List[dict])
async def recommend(req: RecommendRequest, use_rag: bool = Query(False, description="RAG 활성화 여부")):
    """
    recipe_new 테이블 기반 주재료/부재료 가중치 추천 (기본 엔드포인트)
    
    Query Parameters:
        use_rag: True면 FAISS 검색 후 LLM으로 추천 문구 생성 (RAG)
    """
    try:
        # recipe_new 테이블 사용 (FAISS 검색)
        results = recommend_recipes_new_table(
            user_ingredients=req.ingredients,
            user_main_ingredients=req.main_ingredients,
            user_sub_ingredients=req.sub_ingredients,
            main_weight=req.main_weight
        )
        if not results:
            raise HTTPException(status_code=404, detail="조건에 맞는 레시피가 없습니다.")
        
        # RAG 옵션이 활성화된 경우 LLM으로 추천 문구 생성
        results = await apply_rag_if_enabled(
            results=results,
            user_ingredients=req.ingredients,
            use_rag=use_rag
        )
        
        return results
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"추천 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"추천 오류: {str(e)}")

# /recommend/legacy 엔드포인트 (기존 버전) - 제거됨

# /recommend/performance 엔드포인트 (성능 측정)
@router.post("/recommend/performance")
def measure_performance(req: RecommendRequest):
    """recipe_new 테이블 기반 추천 시스템 성능 측정"""
    
    start_time = time.time()
    results = recommend_recipes_new_table(
        user_ingredients=req.ingredients,
        user_main_ingredients=req.main_ingredients,
        user_sub_ingredients=req.sub_ingredients,
        main_weight=req.main_weight
    )
    execution_time = time.time() - start_time
    
    return {
        "ingredients": req.ingredients,
        "main_ingredients": req.main_ingredients,
        "sub_ingredients": req.sub_ingredients,
        "main_weight": req.main_weight,
        "results_count": len(results),
        "execution_time": round(execution_time, 3),
        "results": results[:5]  # 상위 5개만 반환
    }

# /system/status 엔드포인트 (시스템 상태 확인)
@router.get("/system/status")
def system_status():
    """시스템 상태 및 성능 정보"""
    import torch
    
    gpu_info = {}
    
    # CUDA (NVIDIA GPU) 지원 확인
    if torch.cuda.is_available():
        gpu_info = {
            "available": True,
            "type": "CUDA",
            "device_name": torch.cuda.get_device_name(0),
            "device_count": torch.cuda.device_count(),
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
            "max_memory": f"{torch.cuda.max_memory_allocated(0) / 1024**3:.2f} GB"
        }
    # MPS (Apple Silicon GPU) 지원 확인
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        gpu_info = {
            "available": True,
            "type": "MPS",
            "device_name": "Apple Silicon GPU (MPS)",
            "message": "M1/M2/M3 칩의 GPU 가속을 사용 중입니다."
        }
    else:
        gpu_info = {
            "available": False,
            "type": "CPU",
            "message": "GPU를 사용할 수 없습니다. CPU 모드로 실행 중입니다."
        }
    
    return {
        "gpu": gpu_info,
        "timestamp": time.time()
    }

# WebSocket 채팅 엔드포인트
@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    user_id: Optional[str] = Query(None, description="사용자 ID (세션 관리용)"),
    recipe_id: Optional[int] = Query(None, description="레시피 ID (레시피 정보 로드용)")
):
    """
    음성 채팅 WebSocket 엔드포인트
    대화 중 제약사항을 동적으로 감지하여 레시피에 반영
    
    Query Parameters:
        user_id: 사용자 ID (선택적, 세션 관리용)
        recipe_id: 레시피 ID (선택적, 레시피 정보 로드용)
    """
    await websocket.accept()
    logger = logging.getLogger(__name__)
    logger.info(f"클라이언트와 WebSocket 연결 성공. user_id={user_id}, recipe_id={recipe_id}")
    
    AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://203.252.240.65:8001")
    TEMP_DIR = "/tmp"
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    local_temp_files = []
    server1_response_files = []
    
    # 세션 및 레시피 정보 관리
    from .cook_session import session_manager, constraint_parser
    from .rag_prompt_builder import (
        build_llama3_2_prompt,
        create_system_prompt,
        create_step_prompt,
        create_greeting_user_prompt,
        create_next_step_user_prompt,
        constraints_to_dict_list
    )
    
    recipe_data = None
    current_step_index = 0
    
    # 레시피 정보 로드 (recipe_id가 있는 경우)
    if user_id and recipe_id:
        try:
            session = session_manager.create_session(user_id, recipe_id)
            from .cook_api import load_recipe_data
            recipe_data = await load_recipe_data(recipe_id)
            session.recipe_data = recipe_data
            logger.info(f"레시피 정보 로드 완료: {recipe_data.get('title', 'Unknown')}")
        except Exception as e:
            logger.error(f"레시피 정보 로드 실패: {e}")
    
    try:
        # 초기 인사말 전송 (레시피 정보가 있으면 RAG 프롬프트 사용)
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                if recipe_data:
                    # RAG 프롬프트로 인사말 생성
                    recipe_json = {
                        "title": recipe_data.get("title", ""),
                        "ingredients": recipe_data.get("ingredients", []),
                        "steps": recipe_data.get("instructions", []),
                        "content": recipe_data.get("content", "")
                    }
                    
                    # 현재 세션의 제약사항 가져오기
                    constraints = []
                    if user_id:
                        session = session_manager.get_session(user_id)
                        if session:
                            constraints = constraints_to_dict_list(session.constraints)
                    
                    system_prompt = create_system_prompt(recipe_json, constraints)
                    user_prompt = create_greeting_user_prompt()
                    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
                    
                    # ai서버의 /llm-generate에 전송
                    llm_response = await client.post(
                        f"{AI_SERVER_URL}/llm-generate",
                        json={"prompt": final_prompt}
                    )
                    llm_response.raise_for_status()
                    greeting_text = llm_response.json().get("response", "안녕하세요 쿡덕입니다!")
                    
                    # TTS 변환
                    tts_response = await client.post(
                        f"{AI_SERVER_URL}/tts",
                        json={"text": greeting_text}
                    )
                    tts_response.raise_for_status()
                    audio_filename = tts_response.json().get("audio_filename", "")
                else:
                    # 레시피 정보가 없으면 기본 인사말
                    greeting_info_response = await client.post(f"{AI_SERVER_URL}/generate-greeting")
                    greeting_info_response.raise_for_status()
                    greeting_info = greeting_info_response.json()
                    greeting_text = greeting_info["llm_text"]
                    audio_filename = greeting_info["audio_filename"]
                
                await websocket.send_text(json.dumps({"type": "bot_text", "data": greeting_text}))
                await stream_audio(websocket, client, audio_filename)
            logger.info("초기 인사말 처리 완료.")
        except Exception as e:
            logger.error(f"초기 인사말 처리 중 에러 발생: {e}")

        # 사용자 음성 요청 처리 루프
        while True:
            # 1. 클라이언트 음성 수신 및 임시 파일 생성
            wav_data = await websocket.receive_bytes()
            uid = str(uuid.uuid4())
            wav_path = os.path.join(TEMP_DIR, f"{uid}.wav")
            local_temp_files.append(wav_path)
            with open(wav_path, 'wb') as f: f.write(wav_data)
            
            # 2. STT 요청 및 사용자 텍스트 우선 전송
            user_text = ""
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(wav_path, "rb") as f_wav:
                    files = {"audio": (f"{uid}.wav", f_wav, "audio/wav")}
                    stt_response = await client.post(f"{AI_SERVER_URL}/stt", files=files)
                stt_response.raise_for_status()
                user_text = stt_response.json()["text"]
                
                await websocket.send_text(json.dumps({"type": "user_text", "data": user_text}))
                logger.info(f"사용자 텍스트 우선 전송 완료: {user_text}")
            
            # 3. 제약사항 감지 및 세션에 추가
            if user_id:
                session = session_manager.get_session(user_id)
                if session:
                    # 사용자 메시지에서 제약사항 파싱
                    detected_constraints = constraint_parser.parse_message(user_text)
                    if detected_constraints:
                        for constraint in detected_constraints:
                            session_manager.add_constraint(user_id, constraint)
                        logger.info(f"제약사항 감지 및 추가: {[c.type for c in detected_constraints]}")
            
            # 4. LLM/TTS 요청 및 결과 전송
            async with httpx.AsyncClient(timeout=90.0) as client:
                # 레시피 정보가 있고 "다음"이라고 말한 경우
                if recipe_data and user_text.strip() in ["다음", "다음 단계", "다음으로"]:
                    # RAG 프롬프트로 단계 안내 생성
                    session = session_manager.get_session(user_id) if user_id else None
                    current_step_index = session.current_step if session else 0
                    
                    steps = recipe_data.get("instructions", [])
                    if current_step_index < len(steps):
                        current_step_text = steps[current_step_index]
                        
                        recipe_json = {
                            "title": recipe_data.get("title", ""),
                            "ingredients": recipe_data.get("ingredients", []),
                            "steps": recipe_data.get("instructions", []),
                            "content": recipe_data.get("content", "")
                        }
                        
                        # 현재 세션의 제약사항 가져오기
                        constraints = []
                        if session:
                            constraints = constraints_to_dict_list(session.constraints)
                        
                        system_prompt = create_step_prompt(
                            recipe_json,
                            current_step_index,
                            current_step_text,
                            constraints
                        )
                        user_prompt = create_next_step_user_prompt()
                        final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
                        
                        # ai서버의 /llm-generate에 전송
                        llm_response = await client.post(
                            f"{AI_SERVER_URL}/llm-generate",
                            json={"prompt": final_prompt}
                        )
                        llm_response.raise_for_status()
                        bot_response_text = llm_response.json().get("response", current_step_text)
                        
                        # 다음 단계로 이동
                        if session:
                            session.current_step += 1
                    else:
                        bot_response_text = "모든 단계를 완료했습니다!"
                    
                    # TTS 변환
                    tts_response = await client.post(
                        f"{AI_SERVER_URL}/tts",
                        json={"text": bot_response_text}
                    )
                    tts_response.raise_for_status()
                    audio_filename = tts_response.json().get("audio_filename", "")
                else:
                    # 일반 대화 또는 제약사항 언급 시
                    if recipe_data and user_id:
                        # 레시피 정보와 제약사항을 포함한 프롬프트 생성
                        session = session_manager.get_session(user_id)
                        constraints = []
                        if session:
                            constraints = constraints_to_dict_list(session.constraints)
                        
                        recipe_json = {
                            "title": recipe_data.get("title", ""),
                            "ingredients": recipe_data.get("ingredients", []),
                            "steps": recipe_data.get("instructions", []),
                            "content": recipe_data.get("content", "")
                        }
                        
                        system_prompt = create_system_prompt(recipe_json, constraints)
                        final_prompt = build_llama3_2_prompt(system_prompt, user_text)
                        
                        # ai서버의 /llm-generate에 전송
                        llm_response = await client.post(
                            f"{AI_SERVER_URL}/llm-generate",
                            json={"prompt": final_prompt}
                        )
                        llm_response.raise_for_status()
                        bot_response_text = llm_response.json().get("response", "")
                        
                        # TTS 변환
                        tts_response = await client.post(
                            f"{AI_SERVER_URL}/tts",
                            json={"text": bot_response_text}
                        )
                        tts_response.raise_for_status()
                        audio_filename = tts_response.json().get("audio_filename", "")
                    else:
                        # 레시피 정보가 없으면 기본 LLM 응답
                        payload = {"text": user_text}
                        llm_info_response = await client.post(f"{AI_SERVER_URL}/generate-llm-response", json=payload)
                        llm_info_response.raise_for_status()
                        
                        llm_info = llm_info_response.json()
                        bot_response_text = llm_info["llm_text"]
                        audio_filename = llm_info["audio_filename"]
                
                server1_response_files.append(audio_filename)
                
                await websocket.send_text(json.dumps({"type": "bot_text", "data": bot_response_text}))
                logger.info(f"봇 텍스트 전송 완료: {bot_response_text}")

                await stream_audio(websocket, client, audio_filename)

    except WebSocketDisconnect:
        logger.info("클라이언트가 정상적으로 연결을 종료했습니다.")
    except Exception as e:
        logger.error(f"WebSocket 처리 중 예상치 못한 에러 발생: {e}")
    finally:
        # 세션 종료 시 모든 임시 파일 정리
        logger.info("세션 종료. 파일 정리를 시작합니다.")
        for file_path in local_temp_files:
            try:
                if os.path.exists(file_path): os.remove(file_path)
            except Exception as e:
                logger.error(f"로컬 임시 파일 삭제 실패 {file_path}: {e}")
        
        if server1_response_files:
            logger.info(f"서버 1의 응답 오디오 파일 {len(server1_response_files)}개 정리 시작...")
            try:
                async with httpx.AsyncClient() as client:
                    delete_tasks = [client.delete(f"{AI_SERVER_URL}/audio/{fname}") for fname in server1_response_files]
                    await asyncio.gather(*delete_tasks, return_exceptions=True)
                logger.info("서버 1 응답 오디오 파일 정리 완료.")
            except Exception as e:
                 logger.error(f"서버 1 파일 정리 중 에러 발생: {e}")
        
        logger.info("모든 세션 정리 완료.")

async def stream_audio(websocket: WebSocket, client: httpx.AsyncClient, audio_filename: str):
    """오디오를 스트리밍합니다."""
    AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://203.252.240.65:8001")
    async with client.stream("GET", f"{AI_SERVER_URL}/audio/{audio_filename}") as audio_response:
        audio_response.raise_for_status()
        async for chunk in audio_response.aiter_bytes():
            await websocket.send_bytes(chunk)
    
    await websocket.send_text(json.dumps({"type": "event", "data": "TTS_STREAM_END"}))
    logger = logging.getLogger(__name__)
    logger.info(f"오디오 스트리밍 완료: {audio_filename}")

# 레거시 엔드포인트 (기존 recipe 테이블용 - 호환성 유지)
@router.post("/recommend/legacy", response_model=List[dict])
def recommend_legacy(req: RecommendRequest):
    """기존 recipe 테이블 기반 추천 (레거시, 호환성 유지용)"""
    try:
        results = recommend_recipes(req.ingredients)
        if not results:
            raise HTTPException(status_code=404, detail="조건에 맞는 레시피가 없습니다.")
        return results
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"레거시 추천 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"추천 오류: {str(e)}")

# 가중치 기반 추천 엔드포인트 (명시적 - recipe_new 테이블 사용)
@router.post("/recommend/weighted", response_model=List[dict])
async def recommend_weighted(
    req: RecommendRequest,
    use_rag: bool = Query(False, description="RAG 활성화 여부")
):
    """
    recipe_new 테이블 기반 주재료/부재료 가중치 추천 (명시적 엔드포인트)
    
    Query Parameters:
        use_rag: True면 FAISS 검색 후 LLM으로 추천 문구 생성 (RAG)
    """
    try:
        results = recommend_recipes_new_table(
            user_ingredients=req.ingredients,
            user_main_ingredients=req.main_ingredients,
            user_sub_ingredients=req.sub_ingredients,
            main_weight=req.main_weight
        )
        if not results:
            raise HTTPException(status_code=404, detail="조건에 맞는 레시피가 없습니다.")
        
        # RAG 옵션이 활성화된 경우 LLM으로 추천 문구 생성
        results = await apply_rag_if_enabled(
            results=results,
            user_ingredients=req.ingredients,
            use_rag=use_rag
        )
        
        return results
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"가중치 기반 추천 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"추천 오류: {str(e)}")

# recipe_new 테이블 별칭 (이전 버전 호환성)
@router.post("/recommend/new", response_model=List[dict])
async def recommend_new_table(
    req: RecommendRequest,
    use_rag: bool = Query(False, description="RAG 활성화 여부")
):
    """
    recipe_new 테이블 기반 추천 (별칭, /recommend와 동일)
    
    Query Parameters:
        use_rag: True면 FAISS 검색 후 LLM으로 추천 문구 생성 (RAG)
    """
    return await recommend(req, use_rag=use_rag)

# LLM 챗봇 연동 엔드포인트 (Hugging Face 모델 사용)
@router.post("/llama/chat")
def llama_chat(request: dict):
    """LLM 챗봇과 대화 (Hugging Face 모델 사용)"""
    try:
        from .llm_service import get_llm_service
        
        # 메시지 추출
        messages = request.get("messages", [])
        user_message = request.get("message", "")
        
        # 단일 메시지인 경우 리스트로 변환
        if user_message and not messages:
            messages = [
                {"role": "system", "content": "너는 친절한 한국 요리 도우미 셰프야. 사용자의 요리 관련 질문에 도움을 줘."},
                {"role": "user", "content": user_message}
            ]
        
        # LLM 서비스 호출
        llm_service = get_llm_service()
        response_text = llm_service.chat(
            messages=messages,
            max_length=256,
            temperature=0.7
        )
        
        return {
            "response": response_text,
            "model": llm_service.model_name,
            "status": "success"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"LLM 챗봇 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 챗봇 오류: {str(e)}")

@router.post("/llama/recipe-guide")
def llama_recipe_guide(recipe_data: dict):
    """선택된 레시피로 LLM 챗봇 가이드 시작 (Hugging Face 모델 사용)"""
    try:
        from .llm_service import get_llm_service
        
        # 레시피 정보 추출
        recipe_title = recipe_data.get("title", "레시피")
        recipe_ingredients = recipe_data.get("ingredients", "")
        recipe_content = recipe_data.get("content", "")
        
        # 프롬프트 생성
        prompt = f"""다음 레시피에 대한 요리 가이드를 시작합니다.

레시피 이름: {recipe_title}
재료: {recipe_ingredients}
조리법: {recipe_content[:500]}

이 레시피에 대한 친절하고 단계별 요리 가이드를 제공해주세요. 첫 번째 단계부터 시작해서 차근차근 설명해주세요."""
        
        # LLM 서비스 호출
        llm_service = get_llm_service()
        guide_text = llm_service.generate(
            prompt=prompt,
            max_length=512,
            temperature=0.7
        )
        
        return {
            "guide": guide_text,
            "recipe_title": recipe_title,
            "model": llm_service.model_name,
            "status": "success"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"레시피 가이드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"레시피 가이드 오류: {str(e)}")

# 예시 헬로우 엔드포인트(유지)
@router.get("/hello")
def hello():
    return {"message": "Say Hello"}

# LLM 테스트 엔드포인트
@router.post("/llm/test")
def test_llm(request: dict):
    """Hugging Face LLM 테스트 엔드포인트"""
    try:
        from .llm_service import get_llm_service
        
        prompt = request.get("prompt", "안녕하세요!")
        max_length = request.get("max_length", 128)
        temperature = request.get("temperature", 0.7)
        
        llm_service = get_llm_service()
        
        result = llm_service.generate(
            prompt=prompt,
            max_length=max_length,
            temperature=temperature
        )
        
        return {
            "status": "success",
            "model": llm_service.model_name,
            "device": llm_service.device,
            "is_loaded": llm_service.is_loaded(),
            "prompt": prompt,
            "response": result,
            "response_length": len(result)
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"LLM 테스트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 테스트 오류: {str(e)}")

@router.get("/llm/status")
def get_llm_status():
    """LLM 모델 상태 확인"""
    try:
        from .llm_service import get_llm_service
        
        llm_service = get_llm_service()
        
        return {
            "model_name": llm_service.model_name,
            "device": llm_service.device,
            "is_loaded": llm_service.is_loaded(),
            "status": "ready" if llm_service.is_loaded() else "not_loaded"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/predict")
def predict_ingredients(
    file: Optional[UploadFile] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
) -> list:
    """
    프론트엔드 호환용 predict 엔드포인트
    재료 리스트만 반환 (List[str])
    """
    from app.a_vision_pipeline import detect_ingredients as run_vision_pipeline
    
    upload: Optional[UploadFile] = file or image
    if upload is None:
        raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다.")
    
    logger = logging.getLogger(__name__)
    field_name = "file" if upload is file else "image"
    logger.info("=" * 60)
    logger.info(f"/predict 호출 - 필드: {field_name}, 파일: {upload.filename} ({upload.content_type})")
    
    try:
        # content_type 검증: image/로 시작하거나 application/octet-stream 허용
        # (Flutter에서 때때로 octet-stream으로 전송함)
        content_type = upload.content_type or ""
        is_valid_image = (
            content_type.startswith('image/') or 
            content_type == 'application/octet-stream' or
            content_type == ''
        )
        
        # 파일 확장자도 확인
        filename = upload.filename or ""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        has_valid_extension = any(filename.lower().endswith(ext) for ext in valid_extensions)
        
        if not is_valid_image and not has_valid_extension:
            logger.warning(f"잘못된 파일 타입: {content_type}, 파일명: {filename}")
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
        
        image_bytes = upload.file.read()
        
        if len(image_bytes) == 0:
            logger.error("빈 파일")
            raise HTTPException(status_code=400, detail="빈 파일이 업로드되었습니다.")
        
        logger.info(f"이미지 크기: {len(image_bytes)} bytes")
        
        detection = run_vision_pipeline(image_bytes)
        
        ingredients = detection.get("ingredients") or []
        logger.info(f"완료: 총 {len(ingredients)}개 검출")
        logger.info("=" * 60)
        
        # 프론트엔드가 기대하는 형식: 재료 리스트만 반환
        return ingredients
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"오류: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        raise HTTPException(
            status_code=500, 
            detail=f"식재료 추론 중 오류가 발생했습니다: {str(e)}"
        )
    finally:
        if file is not None:
            file.file.close()
        if image is not None and image is not file:
            image.file.close()
