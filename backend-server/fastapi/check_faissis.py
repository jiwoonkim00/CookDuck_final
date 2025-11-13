# 파일 이름: check_faiss.py
# 실행 위치: /Users/server/Desktop/cookDuck_backup/backend-server/fastapi/
# 역할: 'faiss_store' 폴더의 인덱스 파일 존재 여부를 확인합니다.

import os
import sys

# 1. 'fastapi' 폴더의 절대 경로를 기준으로 합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 'faiss_search_new.py'가 찾으려는 파일 경로들을 정의합니다.
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "faiss_store", "index_new.faiss")
FAISS_META_PATH = os.path.join(BASE_DIR, "faiss_store", "metadata_new.pkl")

print(f"--- FAISS 파일 경로 검사 시작 ---")
print(f"기준 폴더: {BASE_DIR}\n")

found_all = True

# --- 3. FAISS 인덱스 파일 검사 ---
print(f"검사 1: 인덱스 파일 (index_new.faiss)")
print(f"  -> 찾는 경로: {FAISS_INDEX_PATH}")
if os.path.exists(FAISS_INDEX_PATH):
    print(f"  ✅ [성공] 파일을 찾았습니다.\n")
else:
    print(f"  🚨 [오류] 파일을 찾을 수 없습니다!\n")
    found_all = False

# --- 4. FAISS 메타데이터 파일 검사 ---
print(f"검사 2: 메타데이터 파일 (metadata_new.pkl)")
print(f"  -> 찾는 경로: {FAISS_META_PATH}")
if os.path.exists(FAISS_META_PATH):
    print(f"  ✅ [성공] 파일을 찾았습니다.\n")
else:
    print(f"  🚨 [오류] 파일을 찾을 수 없습니다!\n")
    found_all = False

# --- 5. 최종 결론 ---
print("--- 검사 완료 ---")
if found_all:
    print("✅ [최종 결론] FAISS 인덱스와 메타데이터 파일이 모두 올바른 위치에 있습니다.")
    print("FAISS 파일 경로는 문제가 없습니다. 'run_rag_test_pjh.py'의 DB 연결(.env)을 확인하세요.")
else:
    print("🚨 [최종 결론] FAISS 파일이 누락되었습니다.")
    print("FAISS 인덱스/메타데이터 파일이 'fastapi/faiss_store/' 폴더에 정확히 있는지 확인하세요.")
    sys.exit(1) # 오류로 종료