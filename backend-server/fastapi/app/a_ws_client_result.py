# -*- coding: utf-8 -*-
# 파일 이름: a_ws_client_result.py
# 실행 위치: '건률컴' 서버 (Mac mini)
# 역할: (최종 수정) 레시피 JSON을 외부에서 받아 동적으로 테스트를 실행합니다.

import asyncio
import websockets
import os
import json
import subprocess # ffmpeg 실행용
import time
from typing import Dict, Any

# --- 설정 ---
# Gateway URL은 환경 변수에서 가져오거나 기본값 사용
import os
GATEWAY_URL = os.getenv("GATEWAY_WS_URL", "ws://127.0.0.1:8009/ws/chat") 

# (수정) "다음" 오디오 파일 하나만 사용합니다.
TEST_WAV_NEXT = "./test_audio/다음.wav"
TEST_PCM_NEXT = "./test_audio/다음.pcm"

# (수정) 수신한 오디오를 저장할 파일 이름
GREETING_AUDIO_OUTPUT = "./output_audio/ws_greeting_output.wav"


async def prepare_pcm_file(source_wav_path: str, output_pcm_path: str):
    """지정된 WAV 파일을 PCM으로 자동 변환합니다. (클라이언트에서 사용)"""
    if not os.path.exists(source_wav_path):
        print(f"🚨 [오류] 원본 WAV 파일({source_wav_path})이 없습니다.")
        return False
    
    output_dir = os.path.dirname(output_pcm_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    print(f"--- PCM 파일 변환: {source_wav_path} -> {output_pcm_path} ---")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", source_wav_path,
                "-f", "s16le", "-ar", "16000", "-ac", "1",
                output_pcm_path
            ],
            check=True, capture_output=True, text=True
        )
        print("✅ PCM 파일 자동 생성 완료.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"🚨 [오류] ffmpeg 변환 실패: {e.stderr}")
        return False
    except FileNotFoundError:
        print("🚨 [오류] 'ffmpeg' 명령어를 찾을 수 없습니다. (brew install ffmpeg)")
        return False

async def receive_bot_response(websocket, output_wav_file):
    """
    봇의 텍스트/음성 응답을 수신하고, '텍스트'를 반환합니다.
    """
    response_audio_bytes = bytearray()
    received_bot_text = ""
    
    output_dir = os.path.dirname(output_wav_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    try:
        while True:
            message = await asyncio.wait_for(websocket.recv(), timeout=120.0) 
            
            if isinstance(message, str):
                data = json.loads(message)
                if data.get("type") == "user_text":
                    print(f"👤 [STT 결과] {data['data']}")
                elif data.get("type") == "bot_text":
                    received_bot_text = data['data']
                    print(f"🤖 [LLM 응답] {received_bot_text}")
                elif data.get("data") == "TTS_STREAM_END":
                    print("✅ 오디오 스트림 수신 완료.")
                    break 
            
            elif isinstance(message, bytes):
                response_audio_bytes.extend(message)
    
    except asyncio.TimeoutError:
        print("🚨 [오류] 120초 이내에 응답을 받지 못했습니다.")
        return None
    except Exception as e:
        print(f"🚨 [수신 오류] {e}")
        return None

    if len(response_audio_bytes) > 0:
        with open(output_wav_file, 'wb') as f:
            f.write(response_audio_bytes)
        print(f"✅ 응답 오디오 저장 완료: {output_wav_file}")
    
    return received_bot_text

# run_websocket_test 함수를 제거하고 동적 입력 함수로 대체합니다.
async def run_websocket_test(selected_recipe_details: Dict[str, Any]):
    """
    외부에서 받은 레시피 JSON을 먼저 전송하고 대화를 반복하는 멀티턴 WebSocket 테스트
    """
    # 레시피 제목을 인스턴스 변수에서 가져와 동적으로 사용
    selected_recipe_title = selected_recipe_details.get("title", "알 수 없는 레시피")
    
    if not await prepare_pcm_file(TEST_WAV_NEXT, TEST_PCM_NEXT): return

    if os.path.exists(GREETING_AUDIO_OUTPUT): os.remove(GREETING_AUDIO_OUTPUT)

    print(f"--- WebSocket 레시피 챗봇 테스트 시작 (연결 대상: {GATEWAY_URL}) ---")
    
    try:
        async with websockets.connect(GATEWAY_URL) as websocket:
            print("✅ 1. 게이트웨이 서버와 WebSocket 연결 성공.")
            
            # --- 1-2단계: 레시피 JSON 전송 (동적 입력 사용) ---
            initial_message_payload = json.dumps({
                "selected_recipe": selected_recipe_details 
            })
            
            await websocket.send(initial_message_payload) 
            print(f"✅ 1-2. 초기 레시피 제목 '{selected_recipe_title}' JSON 전송 완료.")
            
            # --- 2. 초기 인사말 수신 ---
            print(f"\n--- 2. 초기 인사말 수신 대기... ({selected_recipe_title}) ---")
            if await receive_bot_response(websocket, GREETING_AUDIO_OUTPUT) is None:
                return 
            
            # "다음" PCM 데이터 미리 읽기
            with open(TEST_PCM_NEXT, 'rb') as f:
                pcm_data_next = f.read()

            # --- 3단계: "다음" 반복 전송 루프 (동적 루프) ---
            
            step_num = 0
            while True: # 하드코딩된 range 대신 무한 루프 사용
                step_num += 1
                output_file = f"./output_audio/ws_response_step_{step_num}.wav"
                if os.path.exists(output_file): os.remove(output_file)

                await asyncio.sleep(1.5) 
                
                # --- 3.1 '다음' 음성 전송 ---
                print(f"\n--- 3.{step_num} '다음' 음성 전송 ({TEST_WAV_NEXT}) ---")
                await websocket.send(pcm_data_next)
                print(f"✅ '다음' PCM 데이터 전송 완료.")

                # --- 3.2 봇 응답 수신 대기 ---
                print(f"\n--- 4.{step_num} 봇 응답 수신 대기... ---")
                
                bot_text = await receive_bot_response(websocket, output_file)
                
                if bot_text is None:
                    print("🚨 봇 응답 수신 실패. 동적 테스트 루프 종료.")
                    return
                
                # --- 3.3 종료 조건 확인 (동적 로직) ---
                if "요리가 완료되었습니다" in bot_text: 
                    print("\n🎉 레시피가 성공적으로 완료되었습니다! 동적 테스트 루프 종료.")
                    break 
            
            print("\n🎉 WebSocket 멀티턴 파이프라인 테스트 성공!")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\n🚨 [연결 실패] WebSocket 연결이 비정상적으로 닫혔습니다: {e}")
    except Exception as e:
        print(f"\n🚨 [테스트 중 오류 발생] {e}")


def run_test_with_recipe_data(recipe_data: Dict[str, Any]):
    """외부에서 JSON 딕셔너리를 받아 비동기 테스트를 실행하는 메인 함수"""
    asyncio.run(run_websocket_test(recipe_data))

# ================================================================
# 🚨 실행 예시 (테스트를 원하는 레시피 JSON 데이터를 여기에 정의합니다)
# ================================================================

if __name__ == "__main__":
    # 1. 테스트할 레시피 데이터 (어떤 레시피든 가능)
    selected_recipe_details = {
        "id": 531,
        "title": "당근잎 감자전",
        "ingredients": "감자,양파,부침가루,소금,당근잎,당근채",
        "main_ingredients": "감자,양파,부침가루,소금,당근잎,당근채",
        "sub_ingredients": "",
        "tools": "",
        "content": "1. 껍질을 벗긴 감자를 강판에 간다.\n2. 볼에 강판에 간 감자와 다진 양파를 넣고 소금을 살짝 넣어준다.\n3. 볼에 부침가루를 농도에 맞게 넣어 준다.\n4. 당근 잎은 큰 줄기는 때어내어 깨끗하게 손질한다.\n5. 중불로 달군 팬에 감자전 반죽을 넓게 펼친 다음 당근잎과 당근채를  반죽위에 올려 모양을 낸다.\n6. 앞뒤로 뒤집으며 잘 익혀준다.",
    }
    # 2. 동적 테스트 실행
    # 이제 이 함수를 호출하여 원하는 레시피 데이터로 테스트를 시작할 수 있습니다.
    print("--- 테스트 데이터 준비 완료. 동적 테스트 루프 시작 ---")
    run_test_with_recipe_data(selected_recipe_details)