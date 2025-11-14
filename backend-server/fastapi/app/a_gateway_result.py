# # -*- coding: utf-8 -*-
# # 파일 이름: a_gateway_resert.py
# # 실행 위치: '건률컴' 서버
# # 역할: Flutter와 ai서버(8001, 8002) 사이의 '지휘자(Orchestrator)'

# import uvicorn
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# import httpx
# import os
# import uuid
# import logging
# import asyncio
# import json
# import re

# # ==================== 로깅 및 기본 설정 ====================
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# app = FastAPI()

# # ==================== 서버 주소 및 설정 ====================
# AI_SERVER_LLM_URL = os.getenv("AI_SERVER_LLM_URL", "http://127.0.0.1:8001")
# AI_SERVER_TTS_URL = os.getenv("AI_SERVER_TTS_URL", "http://127.0.0.1:8002")
# TEMP_DIR = "/tmp"
# os.makedirs(TEMP_DIR, exist_ok=True)

# # ================================================================
# # 사용자 상태 저장
# # ================================================================
# USER_STATES = {}

# # ================================================================
# # LLM/TTS 호출 유틸
# # ================================================================
# def build_llama3_2_prompt(system_prompt: str, user_prompt: str):
#     prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
#     prompt_str += f"<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>"
#     prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n\n"
#     return prompt_str

# async def call_tts_and_stream(websocket: WebSocket, text: str):
#     async with httpx.AsyncClient(timeout=300.0) as client:
#         tts_payload = {"text": text}
#         async with client.stream("POST", f"{AI_SERVER_TTS_URL}/tts", json=tts_payload) as audio_response:
#             audio_response.raise_for_status()
#             async for chunk in audio_response.aiter_bytes():
#                 await websocket.send_bytes(chunk)
#     await websocket.send_text(json.dumps({"type": "event", "data": "TTS_STREAM_END"}))

# async def call_llm(system_prompt: str, user_prompt: str):
#     final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
#     llm_payload = {"prompt": final_prompt, "max_new_tokens": 100}
#     async with httpx.AsyncClient(timeout=300.0) as client:
#         llm_response = await client.post(f"{AI_SERVER_LLM_URL}/llm-generate", json=llm_payload)
#         llm_response.raise_for_status()
#         return llm_response.json()["response"]

# # ================================================================
# # WebSocket 엔드포인트
# # ================================================================
# @app.websocket("/ws/chat")
# async def websocket_chat_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     logger.info("클라이언트와 WebSocket 연결 성공.")

#     USER_ID = str(uuid.uuid4())

#     # --- 1. 레시피 JSON 수신 및 단계별 초기화 ---
#     try:
#         initial_message = await websocket.receive_text()
#         data = json.loads(initial_message)
#         selected_recipe_data = data.get("selected_recipe")
#         if not selected_recipe_data:
#             raise Exception("클라이언트가 'selected_recipe' 데이터를 제공하지 않았습니다.")

#         title = selected_recipe_data.get("title")
#         content = selected_recipe_data.get("content")
#         if not title or not content:
#             raise Exception("레시피 제목 또는 내용이 JSON 데이터에 포함되어 있지 않습니다.")

#         # ===== 안전한 단계 분리 =====
#         split_result = re.split(r'(?:^|\n)(\d+)\.\s*', content)
#         steps_list = [split_result[i].strip() for i in range(2, len(split_result), 2)]
#         if not steps_list:
#             error_text = f"'{title}' 레시피의 요리 단계를 파싱할 수 없습니다."
#             await websocket.send_text(json.dumps({"type": "bot_text", "data": error_text}))
#             await call_tts_and_stream(websocket, error_text)
#             logger.error(error_text)
#             await websocket.close()
#             return

#         USER_STATES[USER_ID] = {"title": title, "steps": steps_list, "current_step": 0}

#         greeting_text = f"안녕하세요 쿡덕입니다! 사용자님이 선택하신 {title} 레시피를 알려드릴게요! \"다음\" 또는 \"다음단계\"라고 말씀하시면 레시피를 차례대로 안내해 드립니다."
#         await websocket.send_text(json.dumps({"type": "bot_text", "data": greeting_text}))
#         await call_tts_and_stream(websocket, greeting_text)
#         logger.info(f"선택된 레시피: {title}. 초기 인사말 전송 완료. 총 {len(steps_list)}단계.")

#     except WebSocketDisconnect:
#         logger.info(f"클라이언트({USER_ID})가 초기화 중 연결 종료")
#         return
#     except Exception as e:
#         logger.error(f"초기 레시피 수신 및 처리 중 에러: {e}")
#         await websocket.close()
#         return

#     # --- 2. 음성 수신 및 단계별 안내 루프 ---
#     try:
#         while True:
#             pcm_data = await websocket.receive_bytes()
#             uid = str(uuid.uuid4())
#             pcm_path = os.path.join(TEMP_DIR, f"{uid}.pcm")
#             wav_path = os.path.join(TEMP_DIR, f"{uid}.wav")
#             with open(pcm_path, 'wb') as f: f.write(pcm_data)

#             process = await asyncio.create_subprocess_exec(
#                 "ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
#                 "-i", pcm_path, wav_path,
#                 stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
#             )
#             await process.communicate()
#             if process.returncode != 0:
#                 raise Exception("ffmpeg 오디오 변환 실패")

#             async with httpx.AsyncClient(timeout=300.0) as client:
#                 with open(wav_path, "rb") as f_wav:
#                     files = {"audio": (f"{uid}.wav", f_wav, "audio/wav")}
#                     stt_response = await client.post(f"{AI_SERVER_LLM_URL}/stt", files=files)
#                 stt_response.raise_for_status()
#                 user_text = stt_response.json()["text"].strip().lower()
#                 await websocket.send_text(json.dumps({"type": "user_text", "data": user_text}))

#                 state = USER_STATES.get(USER_ID)
#                 if state is None:
#                     raise Exception("사용자 상태 정보(USER_STATE) 없음.")

#                 if user_text in ["다음", "다음 단계", "next"]:
#                     current_step = state["current_step"]
#                     recipe_steps = state["steps"]
#                     if current_step < len(recipe_steps):
#                         bot_response_text = f"{current_step + 1}. {recipe_steps[current_step]}"
#                         state["current_step"] += 1
#                     elif current_step == len(recipe_steps):
#                         bot_response_text = "요리가 완료되었습니다! 맛있게 드세요."
#                         state["current_step"] += 1
#                     else:
#                         bot_response_text = "이미 요리가 완료되었습니다. 다음 명령은 없습니다."
#                     USER_STATES[USER_ID] = state
#                 else:
#                     system_prompt = f"당신은 쿡덕입니다. 지금은 {state['title']} 레시피 안내에만 집중하고 있다고 정중히 답하세요."
#                     bot_response_text = await call_llm(system_prompt, user_text)

#                 await websocket.send_text(json.dumps({"type": "bot_text", "data": bot_response_text}))
#                 await call_tts_and_stream(websocket, bot_response_text)

#     except WebSocketDisconnect:
#         logger.info(f"클라이언트({USER_ID}) 정상 종료")
#         if USER_ID in USER_STATES: del USER_STATES[USER_ID]
#     except Exception as e:
#         logger.error(f"WebSocket 처리 중 에러: {e}")
#         if USER_ID in USER_STATES: del USER_STATES[USER_ID]
#     finally:
#         try:
#             if 'pcm_path' in locals() and os.path.exists(pcm_path): os.remove(pcm_path)
#             if 'wav_path' in locals() and os.path.exists(wav_path): os.remove(wav_path)
#         except Exception:
#             pass
#         logger.info(f"연결 종료 및 임시 파일 정리 완료.")

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8009, reload=False)

# -*- coding: utf-8 -*-
# 파일 이름: a_gateway_resert.py
# 실행 위치: '건률컴' 서버
# 역할: Hybrid AI Gateway (Sequential Parsing + Ingredient Check + Smart RAG)

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

# 사용자 상태 저장소
USER_STATES = {}

# ================================================================
# LLM/TTS 호출 유틸리티
# ================================================================

def build_llama3_2_prompt(system_prompt: str, user_prompt: str):
    """Llama 3.2 프롬프트 포맷 적용"""
    prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    prompt_str += f"<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>"
    prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    return prompt_str

async def call_tts_and_stream(websocket: WebSocket, text: str):
    """TTS 서버 호출 및 오디오 스트리밍"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            tts_payload = {"text": text}
            async with client.stream("POST", f"{AI_SERVER_TTS_URL}/tts", json=tts_payload) as audio_response:
                audio_response.raise_for_status()
                async for chunk in audio_response.aiter_bytes():
                    await websocket.send_bytes(chunk)
        # 스트리밍 종료 이벤트 전송
        await websocket.send_text(json.dumps({"type": "event", "data": "TTS_STREAM_END"}))
    except Exception as e:
        logger.error(f"TTS Streaming Error: {e}")

async def call_llm(system_prompt: str, user_prompt: str):
    """LLM 호출 (Strict Parameters 적용)"""
    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
    llm_payload = {
        "prompt": final_prompt,
        "max_new_tokens": 256,
        "temperature": 0.1,     # 사실 기반 답변 유도 (환각 방지)
        "top_p": 0.9,
        "repetition_penalty": 1.1 
    }
    
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
    logger.info("✅ 클라이언트 연결 성공")
    USER_ID = str(uuid.uuid4())

    # [Phase 1] 초기화: 레시피 데이터 수신 및 파싱
    try:
        initial_message = await websocket.receive_text()
        data = json.loads(initial_message)
        
        # 데이터 추출
        selected_recipe_data = data.get("selected_recipe", data)
        title = selected_recipe_data.get("title")
        content = selected_recipe_data.get("content")
        ingredients = selected_recipe_data.get("ingredients", "정보 없음")
        
        if not title or not content:
            raise Exception("필수 데이터(title, content)가 누락되었습니다.")

        # ----------------------------------------------------------------
        # [핵심 로직] 순차 검증 파싱 (Sequential Validation Logic)
        # 설명: 2.3cm, 1.5배 같은 숫자에 속지 않고 1, 2, 3 순서만 단계로 인정
        # ----------------------------------------------------------------
        # 1. "숫자. 공백" 패턴으로 1차 분리
        raw_split = re.split(r'(\d+)\.\s+', content)
        
        steps_list = []
        current_buffer = raw_split[0] # 첫 부분(제목 등) 버퍼 시작
        expected_step_num = 1         # 1번부터 찾기 시작
        
        i = 1
        while i < len(raw_split):
            num_str = raw_split[i]          # 숫자 (예: '1', '2', '0')
            text_body = raw_split[i+1]      # 내용
            
            # 검증: 기다리던 순서가 맞는가?
            if num_str == str(expected_step_num):
                # 맞다면 이전 버퍼를 저장하고 새 단계 시작
                if current_buffer.strip():
                    steps_list.append(current_buffer.strip())
                current_buffer = text_body
                expected_step_num += 1
            else:
                # 틀리면 (예: 2.3cm의 2) 그냥 텍스트로 간주하고 이어 붙임
                current_buffer += f" {num_str}. {text_body}"
            
            i += 2
        
        # 마지막 버퍼 저장
        if current_buffer.strip():
            steps_list.append(current_buffer.strip())
            
        # 파싱 실패 시 원본 전체 사용 (Fallback)
        if not steps_list:
            steps_list = [content]
        # ----------------------------------------------------------------

        # 상태 저장
        USER_STATES[USER_ID] = {
            "title": title,
            "ingredients": ingredients,
            "steps": steps_list,
            "full_content": content,
            "current_step": 0
        }

        # 안내 인사말 전송
        greeting = (
            f"안녕하세요 쿡덕입니다! 오늘은 '{title}' 요리를 도와드릴게요. "
            f"\"다음\" 또는 \"다음 단계\"라고 말씀하시면 레시피를 차례대로 안내해 드립니다."
        )
        await websocket.send_text(json.dumps({"type": "bot_text", "data": greeting}))
        await call_tts_and_stream(websocket, greeting)

    except Exception as e:
        logger.error(f"Init Error: {e}")
        await websocket.close()
        return

    # [Phase 2] 대화 루프
    try:
        while True:
            # 1. 오디오 수신 및 파일 저장
            pcm_data = await websocket.receive_bytes()
            uid = str(uuid.uuid4())
            pcm_path = os.path.join(TEMP_DIR, f"{uid}.pcm")
            wav_path = os.path.join(TEMP_DIR, f"{uid}.wav")
            with open(pcm_path, 'wb') as f: f.write(pcm_data)

            # 2. FFmpeg 변환
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
                "-i", pcm_path, wav_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            # 3. STT 호출
            user_text = ""
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(wav_path, "rb") as f_wav:
                    files = {"audio": (f"{uid}.wav", f_wav, "audio/wav")}
                    stt_res = await client.post(f"{AI_SERVER_LLM_URL}/stt", files=files)
                user_text = stt_res.json()["text"].strip()
            
            await websocket.send_text(json.dumps({"type": "user_text", "data": user_text}))
            logger.info(f"User: {user_text}")

            state = USER_STATES.get(USER_ID)
            if not state: break

            cmd = user_text.replace(" ", "").lower()
            bot_response = ""

            # [Track A] 명령어 (Fast Track - Navigation)
            if cmd in ["다음", "다음단계", "넥스트", "next"]:
                if state["current_step"] < len(state["steps"]):
                    step_content = state["steps"][state["current_step"]]
                    bot_response = f"{state['current_step'] + 1}단계. {step_content}"
                    state["current_step"] += 1
                else:
                    bot_response = "요리가 끝났습니다. 맛있게 드세요!"
                USER_STATES[USER_ID] = state

            # [Track B] 질문 (Smart Track - RAG with Ingredients)
            else:
                # System Prompt: English Instructions -> Korean Output
                system_prompt = (
                    f"You are a helpful and polite cooking AI assistant named 'CookDuck'.\n"
                    f"You must answer strictly based on the [Recipe Info] below.\n"
                    f"If the user asks about ingredients (e.g., 'Do I need onions?'), check the 'Ingredients List'.\n"
                    f"If the answer is not in the [Recipe Info], politely say you don't know in Korean.\n"
                    f"Do NOT hallucinate or make up information.\n"
                    f"**IMPORTANT: You must answer in KOREAN language (Polite Tone/Honorifics like '해요').**\n\n"
                    f"---------------------\n"
                    f"[Recipe Info]\n"
                    f"Title: {state['title']}\n"
                    f"Ingredients List: {state['ingredients']}\n"
                    f"Cooking Steps:\n{state['full_content']}\n"
                    f"---------------------\n"
                )

                bot_response = await call_llm(system_prompt, user_text)

            # 5. 응답 전송
            await websocket.send_text(json.dumps({"type": "bot_text", "data": bot_response}))
            await call_tts_and_stream(websocket, bot_response)

            # 파일 정리
            if os.path.exists(pcm_path): os.remove(pcm_path)
            if os.path.exists(wav_path): os.remove(wav_path)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        try:
            if 'pcm_path' in locals() and os.path.exists(pcm_path): os.remove(pcm_path)
            if 'wav_path' in locals() and os.path.exists(wav_path): os.remove(wav_path)
        except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009, reload=False)