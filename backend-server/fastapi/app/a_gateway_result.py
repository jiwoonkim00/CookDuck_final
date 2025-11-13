# -*- coding: utf-8 -*-
# 파일 이름: a_gateway_resert.py
# 실행 위치: '건률컴' 서버
# 역할: Flutter와 ai서버(8001, 8002) 사이의 '지휘자(Orchestrator)'

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx
import os
import uuid
import logging
import asyncio
import json
import re

# ==================== 로깅 및 기본 설정 ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

# ==================== 서버 주소 및 설정 ====================
AI_SERVER_LLM_URL = os.getenv("AI_SERVER_LLM_URL", "http://127.0.0.1:8001")
AI_SERVER_TTS_URL = os.getenv("AI_SERVER_TTS_URL", "http://127.0.0.1:8002")
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ================================================================
# 사용자 상태 저장
# ================================================================
USER_STATES = {}

# ================================================================
# LLM/TTS 호출 유틸
# ================================================================
def build_llama3_2_prompt(system_prompt: str, user_prompt: str):
    prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    prompt_str += f"<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>"
    prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    return prompt_str

async def call_tts_and_stream(websocket: WebSocket, text: str):
    async with httpx.AsyncClient(timeout=300.0) as client:
        tts_payload = {"text": text}
        async with client.stream("POST", f"{AI_SERVER_TTS_URL}/tts", json=tts_payload) as audio_response:
            audio_response.raise_for_status()
            async for chunk in audio_response.aiter_bytes():
                await websocket.send_bytes(chunk)
    await websocket.send_text(json.dumps({"type": "event", "data": "TTS_STREAM_END"}))

async def call_llm(system_prompt: str, user_prompt: str):
    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
    llm_payload = {"prompt": final_prompt, "max_new_tokens": 100}
    async with httpx.AsyncClient(timeout=300.0) as client:
        llm_response = await client.post(f"{AI_SERVER_LLM_URL}/llm-generate", json=llm_payload)
        llm_response.raise_for_status()
        return llm_response.json()["response"]

# ================================================================
# WebSocket 엔드포인트
# ================================================================
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("클라이언트와 WebSocket 연결 성공.")

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
        logger.info(f"클라이언트({USER_ID})가 초기화 중 연결 종료")
        return
    except Exception as e:
        logger.error(f"초기 레시피 수신 및 처리 중 에러: {e}")
        await websocket.close()
        return

    # --- 2. 음성 수신 및 단계별 안내 루프 ---
    try:
        while True:
            pcm_data = await websocket.receive_bytes()
            uid = str(uuid.uuid4())
            pcm_path = os.path.join(TEMP_DIR, f"{uid}.pcm")
            wav_path = os.path.join(TEMP_DIR, f"{uid}.wav")
            with open(pcm_path, 'wb') as f: f.write(pcm_data)

            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
                "-i", pcm_path, wav_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode != 0:
                raise Exception("ffmpeg 오디오 변환 실패")

            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(wav_path, "rb") as f_wav:
                    files = {"audio": (f"{uid}.wav", f_wav, "audio/wav")}
                    stt_response = await client.post(f"{AI_SERVER_LLM_URL}/stt", files=files)
                stt_response.raise_for_status()
                user_text = stt_response.json()["text"].strip().lower()
                await websocket.send_text(json.dumps({"type": "user_text", "data": user_text}))

                state = USER_STATES.get(USER_ID)
                if state is None:
                    raise Exception("사용자 상태 정보(USER_STATE) 없음.")

                if user_text in ["다음", "다음 단계", "next"]:
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
                    system_prompt = f"당신은 쿡덕입니다. 지금은 {state['title']} 레시피 안내에만 집중하고 있다고 정중히 답하세요."
                    bot_response_text = await call_llm(system_prompt, user_text)

                await websocket.send_text(json.dumps({"type": "bot_text", "data": bot_response_text}))
                await call_tts_and_stream(websocket, bot_response_text)

    except WebSocketDisconnect:
        logger.info(f"클라이언트({USER_ID}) 정상 종료")
        if USER_ID in USER_STATES: del USER_STATES[USER_ID]
    except Exception as e:
        logger.error(f"WebSocket 처리 중 에러: {e}")
        if USER_ID in USER_STATES: del USER_STATES[USER_ID]
    finally:
        try:
            if 'pcm_path' in locals() and os.path.exists(pcm_path): os.remove(pcm_path)
            if 'wav_path' in locals() and os.path.exists(wav_path): os.remove(wav_path)
        except Exception:
            pass
        logger.info(f"연결 종료 및 임시 파일 정리 완료.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009, reload=False)
