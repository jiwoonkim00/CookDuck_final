# 파일 이름: run_vision_test.py
# 실행 위치: /Users/server/Desktop/cookduck_backup/backend-server/fastapi/
# 역할: (수정본) API 서버 없이, 'detect_ingredients' 함수를 직접 실행합니다.
from dotenv import load_dotenv # <-- [수정] 1. 이 줄을 추가
load_dotenv() # <-- [수정] 2. 이 줄을 추가 (다른 import보다 먼저 실행)

import sys
import os
import pprint
from typing import Union # Python 3.9 호환성용

def main():
    """
    테스트를 실행하는 메인 함수
    """
    
    # --- 1. 테스트할 이미지 파일 경로 설정 ---
    IMAGE_PATH = "/Users/server/Desktop/cookduck_backup/backend-server/sample.jpg"

    if not os.path.exists(IMAGE_PATH):
        print(f"🚨 [오류] 테스트 이미지 파일을 찾을 수 없습니다: {IMAGE_PATH}")
        sys.exit(1)

    # --- 2. 'app' 폴더 내부의 핵심 로직(detect_ingredients) 임포트 ---
    try:
        # [수정] 'run_vision_pipeline' 대신 'detect_ingredients'를 임포트
        from app.vision_pipeline import detect_ingredients
    
    except ImportError as e:
        print(f"🚨 [오류] 모듈 임포트 실패: {e}")
        print("이 스크립트를 'fastapi' 폴더에서 실행 중인지,")
        print("app/vision_pipeline.py의 'from vision_task...' 경로가 올바른지 확인하세요.")
        sys.exit(1)
    except Exception as e:
        print(f"🚨 [오류] 모듈 로드 중 알 수 없는 오류 발생: {e}")
        sys.exit(1)

    # --- 3. 이미지 파일을 읽고 파이프라인 실행 ---
    print(f"--- 1. 이미지 파일 로드 ---")
    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()
    print(f"✅ 이미지 로드 완료 ({len(image_bytes)} bytes)")

    print(f"--- 2. 비전 파이프라인 ('detect_ingredients') 실행 시작... ---")
    try:
        # [수정] 'detect_ingredients' 함수를 직접 호출
        detection_result = detect_ingredients(image_bytes)
        
        print("\n--- 3. [최종 성공] 파이프라인 결과 ---")
        pprint.pprint(detection_result)

    except ValueError as e:
        print(f"\n🚨🚨🚨 [치명적 오류] 파이프라인 실행 실패 🚨🚨🚨")
        print(f"오류 메시지: {e}")
        
        # (중요) 이 오류는 다음 단계에서 발생할 것입니다.
        if "'None' does not exist" in str(e) or "환경 변수가 설정되지 않았습니다" in str(e):
            print("\n--- [해결책] ---")
            print("YOLO/VLM 모델 경로가 설정되지 않았습니다.")
            print("스크립트를 실행하기 '전'에, 터미널에서 'export' 명령어를 실행하세요.")
            print("예시:")
            print("  export YOLO_MODEL_PATH=\"/Users/server/Desktop/models/yolo.pt\"")
            print("  export VLM_MODEL_ID=\"Salesforce/blip-image-captioning-large\"")
        else:
             print(f"예상치 못한 ValueError: {e}")
    except Exception as e:
        print(f"\n🚨🚨🚨 [알 수 없는 오류] 🚨🚨🚨")
        print(f"오류: {e}")

if __name__ == "__main__":
    main()