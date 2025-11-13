# 파일 이름: run_rag_test_csv.py
# 실행 위치: /Users/server/Desktop/cookDuck_backup/backend-server/fastapi/
# 역할: (DB/FAISS 미사용) CSV 파일과 단순 재료 매칭으로 RAG 테스트

import os
import sys
import re
import pprint
import pandas as pd
from typing import List, Dict, Tuple, Set, Union # Python 3.9 호환성용

# --- [1. Segfault 해결 코드] ---
# (pandas/numpy가 내부적으로 PyTorch/MKL과 충돌하는 것을 방지)
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

# --- [2. .env 파일 로드] ---
# (DB 접속엔 안 쓰지만, API 키 등을 위해 로드)
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ .env 파일 로드 성공: {dotenv_path}")
else:
    print(f"🚨 [경고] .env 파일을 찾을 수 없습니다.")

# --- [3. CSV 파일 및 경로 설정] ---
CSV_PATH = "/Users/server/Desktop/cookDuck_backup/backend-server/fastapi/recipe_final.csv"
RECIPE_DF = None # CSV 데이터를 저장할 전역 변수

# --- [4. 'faiss_search_new.py'에서 헬퍼 함수 복사] ---
# (DB/FAISS 의존성이 없는 'extract_name' 함수만 가져옴)

SYNONYM_MAP = {
    "계란": "달걀", "달걀": "달걀", "진간장": "간장", "간장": "간장",
    "설탕": "설탕", "백설탕": "설탕", "식용유": "식용유", "카놀라유": "식용유",
    "대파": "파", "쪽파": "파", "파": "파", "양파": "양파",
    "감자": "감자", "당근": "당근", "소금": "소금", "후추": "후추",
    "마늘": "마늘", "다진마늘": "마늘", "고추장": "고추장",
    "고춧가루": "고춧가루", "참기름": "참기름", "버터": "버터",
}

def extract_name(ingredient: str) -> str:
    """재료명 정제 (faiss_search_new.py에서 복사)"""
    cleaned = re.sub(r'[^가-힣a-zA-Z]', '', str(ingredient))
    prefixes = ['진', '생', '말린', '건', '다진', '채썬', '썰은', '썬', '새', '조리']
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return SYNONYM_MAP.get(cleaned, cleaned) if cleaned else ingredient

# --- [5. CSV 로드 함수] ---
def load_csv_database():
    """서버 시작 시 CSV 파일을 메모리로 로드합니다."""
    global RECIPE_DF
    try:
        RECIPE_DF = pd.read_csv(CSV_PATH, encoding='utf-8')
    except UnicodeDecodeError:
        logger.warning("UTF-8 로드 실패, CP949(한글 Windows)로 재시도...")
        try:
            RECIPE_DF = pd.read_csv(CSV_PATH, encoding='cp949')
        except Exception as e:
            print(f"🚨 [치명적 오류] CSV 파일 로드 실패! {e}")
            return False
    except FileNotFoundError:
        print(f"🚨 [치명적 오류] CSV 파일을 찾을 수 없습니다! 경로: {CSV_PATH}")
        return False
    
    if '재료명' not in RECIPE_DF.columns or '레시피 이름' not in RECIPE_DF.columns:
        print("🚨 [치명적 오류] CSV에 '레시피 이름' 또는 '재료명' 컬럼이 없습니다.")
        return False

    # (중요) CSV의 '재료명'을 미리 'set'으로 변환하여 검색 속도 향상
    print("... CSV '재료명' 컬럼을 Set으로 변환 중 ...")
    RECIPE_DF['ingredients_set'] = RECIPE_DF['재료명'].apply(
        lambda x: {extract_name(i.strip()) for i in str(x).split(',')}
    )
    print(f"✅ CSV 파일 로드 및 'ingredients_set' 생성 성공. 총 {len(RECIPE_DF)}개 레시피.")
    return True

# --- [6. "DB 없는" RAG 매칭 함수] ---
def recommend_recipes_from_csv(user_set: Set[str], top_k: int = 5) -> List[Dict]:
    """
    (DB 미사용) 로드된 DataFrame을 순회하며 단순 재료 매칭(Overlap) 점수를 계산합니다.
    """
    if RECIPE_DF is None:
        raise Exception("CSV 데이터가 로드되지 않았습니다.")

    scores = []

    # DataFrame을 순회하며 점수 계산
    for index, row in RECIPE_DF.iterrows():
        recipe_set = row['ingredients_set']
        
        # (핵심) 사용자가 가진 재료와 레시피의 재료가 얼마나 겹치는지 확인
        matched_ingredients = user_set.intersection(recipe_set)
        
        # (점수 로직) 겹치는 재료의 개수를 점수로 사용
        score = len(matched_ingredients)
        
        if score > 0:
            scores.append((score, index, list(matched_ingredients)))
    
    # 점수가 높은 순(내림차순)으로 정렬
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Top K 결과 추출
    top_results = []
    for score, index, matched in scores[:top_k]:
        # .iloc[index]를 사용해 원본 DataFrame의 '행 전체'를 dict로 변환
        result_row_dict = RECIPE_DF.iloc[index].to_dict()
        
        # (부가 정보) 점수와 매칭된 재료를 결과에 추가
        result_row_dict["matching_score"] = score
        result_row_dict["matched_items"] = matched
        
        top_results.append(result_row_dict)
        
    return top_results

# --- [7. 메인 실행 함수] ---
def main():
    """
    RAG + DB(CSV) 검색 테스트를 실행하는 메인 함수
    """
    # 0. CSV 로드
    if not load_csv_database():
        sys.exit(1) # CSV 로드 실패 시 종료

    # 1. (가상) Vision API 응답 결과
    vision_raw_text = "당근, 대파, 오렌지, 토마토, 감자, 애호박, 피망, 버섯, 오이, 콩, 식빵, 크래커, 라면, 파스타, 팝콘"
    print(f"\n--- 1. Vision API 결과 (raw_text) ---")
    print(f"{vision_raw_text}\n")

    # 2. raw_text를 Set[str]로 변환
    try:
        user_ingredients_set = {extract_name(item.strip()) for item in vision_raw_text.split(',')}
        print(f"--- 2. RAG 입력용 재료 Set ---")
        print(f"{user_ingredients_set}\n")
    except Exception as e:
        print(f"🚨 [오류] raw_text 파싱 실패: {e}")
        sys.exit(1)

    # 3. RAG(CSV) 검색 실행
    print(f"--- 3. RAG (CSV 단순 매칭) 검색 시작... ---")
    try:
        # (모듈 3 실행) DB 대신 CSV 매칭 함수 호출
        ranked_recipes = recommend_recipes_from_csv(
            user_set=user_ingredients_set,
            top_k=5 
        )
        
        print("✅ RAG (CSV) 검색 성공.")
        print("--- 4. [최종 성공] RAG 검색 결과 (Top 5 - 행 전체) ---")
        
        if not ranked_recipes:
            print("매칭되는 레시피가 없습니다.")
            sys.exit(0)

        for i, recipe_row in enumerate(ranked_recipes):
            print(f"\n--- [순위 {i+1}] (Score: {recipe_row['matching_score']}) ---")
            print(f"  제목: {recipe_row.get('레시피 이름')}")
            print(f"  매칭된 재료: {recipe_row.get('matched_items')}")
            # (행 전체를 보려면 pprint.pprint(recipe_row) 사용)
            pprint.pprint(recipe_row) 

    except Exception as e:
        print(f"🚨 [오류] RAG 검색 중 오류 발생:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()