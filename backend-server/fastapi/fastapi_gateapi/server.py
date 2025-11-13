# /CookDuck/backend-server/fastapi/fastapi_gateapi/server.py
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx
import os
import uuid
import logging
import asyncio
import json
import re

# --- 기본 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://203.252.240.65:8001")
AI_SERVER_LLM_URL = os.getenv("AI_SERVER_LLM_URL", AI_SERVER_URL)
AI_SERVER_TTS_URL = os.getenv("AI_SERVER_TTS_URL", AI_SERVER_URL.replace(":8001", ":8002") if ":8001" in AI_SERVER_URL else AI_SERVER_URL)
logger.info(f"AI 서버 주소: {AI_SERVER_URL}")
logger.info(f"AI LLM 서버 주소: {AI_SERVER_LLM_URL}")
logger.info(f"AI TTS 서버 주소: {AI_SERVER_TTS_URL}")
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ================================================================
# 사용자 상태 저장 (레시피 챗봇용)
# ================================================================
USER_STATES = {}

# ================================================================
# LLM/TTS 호출 유틸 (레시피 챗봇용)
# ================================================================
def build_llama3_2_prompt(system_prompt: str, user_prompt: str):
    prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    prompt_str += f"<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>"
    prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    return prompt_str

async def call_tts_and_stream(websocket: WebSocket, text: str):
    """TTS 호출 및 오디오 스트리밍 (레시피 챗봇용)"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            tts_payload = {"text": text}
            async with client.stream("POST", f"{AI_SERVER_TTS_URL}/tts", json=tts_payload) as audio_response:
                audio_response.raise_for_status()
                async for chunk in audio_response.aiter_bytes():
                    await websocket.send_bytes(chunk)
        await websocket.send_text(json.dumps({"type": "event", "data": "TTS_STREAM_END"}))
    except Exception as e:
        logger.error(f"TTS 호출 실패: {e}")

async def call_llm(system_prompt: str, user_prompt: str):
    """LLM 호출 (레시피 챗봇용)"""
    try:
        final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
        llm_payload = {"prompt": final_prompt, "max_new_tokens": 100}
        async with httpx.AsyncClient(timeout=300.0) as client:
            llm_response = await client.post(f"{AI_SERVER_LLM_URL}/llm-generate", json=llm_payload)
            llm_response.raise_for_status()
            return llm_response.json()["response"]
    except Exception as e:
        logger.error(f"LLM 호출 실패: {e}")
        return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."

# 헬스체크 엔드포인트
@app.get("/")
async def root():
    return {"message": "FastAPI GateAPI 서버가 실행 중입니다.", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "fastapi-gateapi"}

async def stream_audio(websocket: WebSocket, client: httpx.AsyncClient, audio_filename: str):
    """오디오를 스트리밍합니다."""
    async with client.stream("GET", f"{AI_SERVER_URL}/audio/{audio_filename}") as audio_response:
        audio_response.raise_for_status()
        async for chunk in audio_response.aiter_bytes():
            await websocket.send_bytes(chunk)
    
    await websocket.send_text(json.dumps({"type": "event", "data": "TTS_STREAM_END"}))
    logger.info(f"오디오 스트리밍 완료: {audio_filename}")

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("클라이언트와 WebSocket 연결 성공.")
    
    local_temp_files = []
    server1_response_files = []
    
    try:
        # --- 초기 인사말 전송 ---
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
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

        # --- 사용자 음성 요청 처리 루프 ---
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
                
                # [핵심] 사용자 텍스트를 클라이언트에 우선 전송
                await websocket.send_text(json.dumps({"type": "user_text", "data": user_text}))
                logger.info(f"사용자 텍스트 우선 전송 완료: {user_text}")
            
            # 3. LLM/TTS 요청 및 결과 전송
            async with httpx.AsyncClient(timeout=90.0) as client:
                payload = {"text": user_text}
                llm_info_response = await client.post(f"{AI_SERVER_URL}/generate-llm-response", json=payload)
                llm_info_response.raise_for_status()
                
                llm_info = llm_info_response.json()
                bot_response_text = llm_info["llm_text"]
                audio_filename = llm_info["audio_filename"]
                
                server1_response_files.append(audio_filename)
                
                # [핵심] 봇의 답변 텍스트를 나중에 전송
                await websocket.send_text(json.dumps({"type": "bot_text", "data": bot_response_text}))
                logger.info(f"봇 텍스트 전송 완료: {bot_response_text}")

                # 오디오 스트리밍
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

# ================================================================
# 레시피 기반 챗봇 WebSocket 엔드포인트
# ================================================================
@app.websocket("/ws/recipe-chat")
async def websocket_recipe_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("레시피 챗봇: 클라이언트와 WebSocket 연결 성공.")

    USER_ID = str(uuid.uuid4())

    # --- 1. 레시피 JSON 수신 및 단계별 초기화 ---
    try:
        initial_message = await websocket.receive_text()
        data = json.loads(initial_message)
        selected_recipe_data = data.get("selected_recipe")
        if not selected_recipe_data:
            raise Exception("클라이언트가 'selected_recipe' 데이터를 제공하지 않았습니다.")

        title = selected_recipe_data.get("title")
        content = selected_recipe_data.get("content")
        if not title or not content:
            raise Exception("레시피 제목 또는 내용이 JSON 데이터에 포함되어 있지 않습니다.")

        # ===== 안전한 단계 분리 =====
        split_result = re.split(r'(?:^|\n)(\d+)\.\s*', content)
        steps_list = [split_result[i].strip() for i in range(2, len(split_result), 2)]
        if not steps_list:
            error_text = f"'{title}' 레시피의 요리 단계를 파싱할 수 없습니다."
            await websocket.send_text(json.dumps({"type": "bot_text", "data": error_text}))
            await call_tts_and_stream(websocket, error_text)
            logger.error(error_text)
            await websocket.close()
            return

        USER_STATES[USER_ID] = {"title": title, "steps": steps_list, "current_step": 0}

        greeting_text = f"안녕하세요 쿡덕입니다! 사용자님이 선택하신 {title} 레시피를 알려드릴게요! \"다음\" 또는 \"다음단계\"라고 말씀하시면 레시피를 차례대로 안내해 드립니다."
        await websocket.send_text(json.dumps({"type": "bot_text", "data": greeting_text}))
        await call_tts_and_stream(websocket, greeting_text)
        logger.info(f"선택된 레시피: {title}. 초기 인사말 전송 완료. 총 {len(steps_list)}단계.")

    except WebSocketDisconnect:
        logger.info(f"레시피 챗봇: 클라이언트({USER_ID})가 초기화 중 연결 종료")
        return
    except Exception as e:
        logger.error(f"레시피 챗봇: 초기 레시피 수신 및 처리 중 에러: {e}")
        await websocket.close()
        return

    # --- 2. 음성 수신 및 단계별 안내 루프 ---
    local_temp_files = []  # 임시 파일 추적용
    try:
        while True:
            # WAV 데이터 수신 (Flutter에서 WAV로 전송)
            logger.info("레시피 챗봇: 오디오 데이터 수신 대기 중...")
            wav_path = None
            try:
                # 메시지 타입 확인 (바이너리 또는 텍스트)
                message = await websocket.receive()
                logger.info(f"레시피 챗봇: 메시지 수신 (keys: {list(message.keys())})")
                
                if "bytes" in message:
                    audio_data = message["bytes"]
                    logger.info(f"레시피 챗봇: 오디오 데이터 수신 완료 ({len(audio_data)} bytes)")
                    
                    # WAV 파일로 저장
                    uid = str(uuid.uuid4())
                    wav_path = os.path.join(TEMP_DIR, f"{uid}.wav")
                    try:
                        with open(wav_path, 'wb') as f: 
                            f.write(audio_data)
                        local_temp_files.append(wav_path)
                        file_size = os.path.getsize(wav_path)
                        logger.info(f"레시피 챗봇: 오디오 파일 저장 완료 ({wav_path}, 크기: {file_size} bytes)")
                    except Exception as file_err:
                        logger.error(f"레시피 챗봇: 오디오 파일 저장 실패: {file_err}")
                        continue
                elif "text" in message:
                    # 텍스트 메시지가 오면 무시하고 다시 대기
                    logger.warning(f"레시피 챗봇: 예상치 못한 텍스트 메시지 수신: {message['text'][:100]}")
                    continue
                else:
                    logger.warning(f"레시피 챗봇: 알 수 없는 메시지 타입: {message}")
                    continue
            except WebSocketDisconnect:
                logger.info(f"레시피 챗봇: 클라이언트({USER_ID})가 연결 종료")
                break  # 루프 종료
            except RuntimeError as runtime_err:
                # "Cannot call receive once a disconnect message has been received" 에러 처리
                if "disconnect" in str(runtime_err).lower():
                    logger.info(f"레시피 챗봇: WebSocket 연결이 이미 종료됨 ({USER_ID})")
                    break  # 루프 종료
                else:
                    logger.error(f"레시피 챗봇: RuntimeError 발생: {runtime_err}", exc_info=True)
                    continue
            except Exception as receive_error:
                logger.error(f"레시피 챗봇: 메시지 수신 중 에러: {receive_error}", exc_info=True)
                # 연결이 끊어진 경우 루프 종료
                if "disconnect" in str(receive_error).lower() or "receive" in str(receive_error).lower():
                    logger.info(f"레시피 챗봇: 연결 종료로 인한 에러, 루프 종료")
                    break
                continue
            
            if not wav_path or not os.path.exists(wav_path):
                logger.error("레시피 챗봇: WAV 파일이 생성되지 않았습니다.")
                continue

            # STT 요청
            logger.info(f"레시피 챗봇: STT 서버로 요청 전송 중... ({AI_SERVER_LLM_URL}/stt)")
            user_text = None
            try:
                if not os.path.exists(wav_path):
                    logger.error(f"레시피 챗봇: WAV 파일이 존재하지 않음: {wav_path}")
                    continue
                
                file_size = os.path.getsize(wav_path)
                logger.info(f"레시피 챗봇: STT 요청 시작 (파일: {wav_path}, 크기: {file_size} bytes)")
                
                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                    logger.info(f"레시피 챗봇: STT POST 요청 준비 중... (파일명: {uid}.wav)")
                    with open(wav_path, "rb") as f_wav:
                        files = {"audio": (f"{uid}.wav", f_wav, "audio/wav")}
                        logger.info(f"레시피 챗봇: STT POST 요청 전송 중... (URL: {AI_SERVER_LLM_URL}/stt)")
                        stt_response = await client.post(f"{AI_SERVER_LLM_URL}/stt", files=files)
                        logger.info(f"레시피 챗봇: STT 응답 수신 (상태 코드: {stt_response.status_code})")
                    
                    stt_response.raise_for_status()
                    response_json = stt_response.json()
                    logger.info(f"레시피 챗봇: STT 응답 JSON: {response_json}")
                    user_text = response_json.get("text", "").strip().lower()
                    logger.info(f"레시피 챗봇: STT 결과: '{user_text}'")
            except httpx.TimeoutException as timeout_err:
                logger.error(f"레시피 챗봇: STT 요청 타임아웃 (30초 초과): {timeout_err}")
                await websocket.send_text(json.dumps({"type": "bot_text", "data": "음성 인식 서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."}))
                await call_tts_and_stream(websocket, "음성 인식 서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
                continue
            except httpx.ConnectError as conn_err:
                logger.error(f"레시피 챗봇: STT 서버 연결 실패: {conn_err}")
                await websocket.send_text(json.dumps({"type": "bot_text", "data": "음성 인식 서버에 연결할 수 없습니다. 네트워크를 확인해주세요."}))
                await call_tts_and_stream(websocket, "음성 인식 서버에 연결할 수 없습니다. 네트워크를 확인해주세요.")
                continue
            except Exception as stt_error:
                logger.error(f"레시피 챗봇: STT 요청 실패: {stt_error}", exc_info=True)
                await websocket.send_text(json.dumps({"type": "bot_text", "data": "음성 인식에 실패했습니다. 다시 시도해주세요."}))
                await call_tts_and_stream(websocket, "음성 인식에 실패했습니다. 다시 시도해주세요.")
                continue
            
            if not user_text or len(user_text.strip()) == 0:
                logger.warning("레시피 챗봇: STT 결과가 비어있음")
                await websocket.send_text(json.dumps({"type": "bot_text", "data": "음성을 인식하지 못했습니다. 다시 말씀해주세요."}))
                await call_tts_and_stream(websocket, "음성을 인식하지 못했습니다. 다시 말씀해주세요.")
                continue
            
            # 사용자 텍스트 전송
            await websocket.send_text(json.dumps({"type": "user_text", "data": user_text}))

            state = USER_STATES.get(USER_ID)
            if state is None:
                raise Exception("사용자 상태 정보(USER_STATE) 없음.")

            # 레시피 단계 처리
            if user_text in ["다음", "다음 단계", "next", "다음단계"]:
                current_step = state["current_step"]
                recipe_steps = state["steps"]
                if current_step < len(recipe_steps):
                    bot_response_text = f"{current_step + 1}. {recipe_steps[current_step]}"
                    state["current_step"] += 1
                elif current_step == len(recipe_steps):
                    bot_response_text = "요리가 완료되었습니다! 맛있게 드세요."
                    state["current_step"] += 1
                else:
                    bot_response_text = "이미 요리가 완료되었습니다. 다음 명령은 없습니다."
                USER_STATES[USER_ID] = state
            else:
                # LLM을 통한 일반 응답
                system_prompt = f"당신은 쿡덕입니다. 지금은 {state['title']} 레시피 안내에만 집중하고 있다고 정중히 답하세요."
                bot_response_text = await call_llm(system_prompt, user_text)

            # 봇 응답 전송
            logger.info(f"레시피 챗봇: 봇 응답 생성 완료: '{bot_response_text[:50]}...'")
            await websocket.send_text(json.dumps({"type": "bot_text", "data": bot_response_text}))
            logger.info("레시피 챗봇: 봇 텍스트 메시지 전송 완료, TTS 시작")
            await call_tts_and_stream(websocket, bot_response_text)
            logger.info("레시피 챗봇: TTS 스트리밍 완료")

    except WebSocketDisconnect:
        logger.info(f"레시피 챗봇: 클라이언트({USER_ID}) 정상 종료")
        if USER_ID in USER_STATES: 
            del USER_STATES[USER_ID]
    except Exception as e:
        logger.error(f"레시피 챗봇: WebSocket 처리 중 에러: {e}", exc_info=True)
        if USER_ID in USER_STATES: 
            del USER_STATES[USER_ID]
    finally:
        # 임시 파일 정리
        try:
            for temp_file in local_temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"레시피 챗봇: 임시 파일 삭제 완료: {temp_file}")
        except Exception as cleanup_error:
            logger.warning(f"레시피 챗봇: 임시 파일 정리 중 에러: {cleanup_error}")
        logger.info(f"레시피 챗봇: 연결 종료 및 임시 파일 정리 완료.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
