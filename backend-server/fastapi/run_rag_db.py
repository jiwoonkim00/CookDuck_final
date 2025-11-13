# 파일 이름: run_rag_db.py (출력부만 JSON 형식으로 수정)
# 실행 위치: /Users/server/Desktop/cookDuck_backup/backend-server/fastapi/

import os
import sys
import re
import pprint
import traceback
from typing import List, Dict, Tuple, Union, Set

# --- [1. Segfault 해결 코드] ---
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")

# --- [2. 필요한 라이브러리] ---
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ .env 파일 로드 성공: {dotenv_path}")
else:
    print(f"🚨 [경고] .env 파일을 찾을 수 없습니다.")

# --- 이하 원본 코드 동일 ---
def get_faiss_path(filename: str) -> str:
    path = f"faiss_store/{filename}"
    if os.path.exists(path): return path
    raise FileNotFoundError(f"FAISS 파일을 찾을 수 없습니다: {path}")

try:
    INDEX_SAVE_PATH = get_faiss_path("index_new.faiss")
    META_SAVE_PATH = get_faiss_path("metadata_new.pkl")
    model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
    index = faiss.read_index(INDEX_SAVE_PATH)
    with open(META_SAVE_PATH, "rb") as f: metadata = pickle.load(f)
    print(f"✅ FAISS 인덱스 로드 완료 (경로: {INDEX_SAVE_PATH})")
except Exception as e:
    print(f"🚨 [치명적 오류] FAISS 인덱스 로드 실패: {e}")
    sys.exit(1)

try:
    DB_HOST = "127.0.0.1" 
    DB_PORT = "3307"
    DB_URL = f"mysql+pymysql://root:root@{DB_HOST}:{DB_PORT}/recipe_db"
    local_engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=local_engine, autocommit=False, autoflush=False)
    print(f"✅ DB 연결 엔진 생성 성공 (대상: {DB_HOST}:{DB_PORT})")
except Exception as e:
    print(f"🚨 [오류] DB 엔진 생성 실패: {e}")
    sys.exit(1)

SYNONYM_MAP = {
    "계란": "달걀", "달걀": "달걀", "진간장": "간장", "간장": "간장",
    "설탕": "설탕", "백설탕": "설탕", "식용유": "식용유", "카놀라유": "식용유",
    "대파": "파", "쪽파": "파", "파": "파", "양파": "양파",
    "감자": "감자", "당근": "당근", "소금": "소금", "후추": "후추",
    "마늘": "마늘", "다진마늘": "마늘", "고추장": "고추장",
    "고춧가루": "고춧가루", "참기름": "참기름", "버터": "버터",
}
def extract_name(ingredient: str) -> str:
    cleaned = re.sub(r'[^가-힣a-zA-Z]', '', str(ingredient))
    prefixes = ['진', '생', '말린', '건', '다진', '채썬', '썰은', '썬', '새', '조리']
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return SYNONYM_MAP.get(cleaned, cleaned) if cleaned else ingredient

RECIPE_INGREDIENT_MAP = {}
try:
    print("... DB에서 'recipe_ingredient_cleaned' 테이블 로드 시작 ...")
    session = SessionLocal()
    query = text('SELECT recipe_code, ingredient_name, ingredient_type_name FROM recipe_ingredient_cleaned')
    result = session.execute(query)
    row_count = 0
    for row in result.fetchall():
        row_count += 1
        recipe_code = row.recipe_code
        if recipe_code not in RECIPE_INGREDIENT_MAP:
            RECIPE_INGREDIENT_MAP[recipe_code] = {"main": set(), "sub": set()}
        cleaned_name = extract_name(row.ingredient_name)
        if row.ingredient_type_name== '주재료' or row.ingredient_type_name == 'MAIN':
            RECIPE_INGREDIENT_MAP[recipe_code]["main"].add(cleaned_name)
        else:
            RECIPE_INGREDIENT_MAP[recipe_code]["sub"].add(cleaned_name)
    session.close()
    if row_count == 0:
        raise Exception("'recipe_ingredient_cleaned' 테이블에서 데이터를 가져오지 못했습니다.")
    print(f"✅ 재료 가중치 DB 로드 완료 (총 {len(RECIPE_INGREDIENT_MAP)}개 레시피)")
except Exception as e:
    print(f"🚨 [치명적 오류] 테이블 로드 실패: {e}")
    if 'session' in locals() and session: session.close()
    sys.exit(1)

def calculate_weighted_score(
    user_set: Set[str], 
    recipe_main_set: Set[str], 
    recipe_sub_set: Set[str],
    distance: float,
    main_weight: float = 2.0,
    sub_weight: float = 1.0
) -> Tuple[float, List[str], List[str]]:
    matched_main = list(user_set.intersection(recipe_main_set))
    matched_sub = list(user_set.intersection(recipe_sub_set))
    score = (len(matched_main) * main_weight) + (len(matched_sub) * sub_weight)
    dist_score = 1 / (1 + distance)
    final_score = (score * 100) + dist_score
    return final_score, matched_main, matched_sub

def classify_user_ingredients(ingredients: List[str]) -> Set[str]:
    return {extract_name(ing) for ing in ingredients}
    

def recommend_recipes_new_table(user_ingredients: List[str], top_k: int = 538) -> List[Dict]:
    if index is None: raise Exception("FAISS 인덱스가 로드되지 않았습니다.")
    print(f"\n=== recipe_new 테이블 추천 시작 ===")
    print(f"사용자 재료 (List): {user_ingredients}")
    user_set = classify_user_ingredients(user_ingredients)
    print(f"사용자 재료 (Set): {user_set}")

    all_ingredients_text = ", ".join(user_set)
    query = f"이 요리의 재료는 {all_ingredients_text}입니다."
    emb = model.encode([query]).astype("float32")
    D, I = index.search(emb, top_k)
    print(f"FAISS 검색 결과: {len(I[0])}개")

    session = SessionLocal()
    try:
        best = {}
        for idx, dist in zip(I[0], D[0]):
            if idx < len(metadata):
                rid = metadata[idx].get("id")
                if rid and (rid not in best or dist < best[rid][1]):
                    best[rid] = (idx, dist)

        results = []
        seen = set()

        for idx, dist in sorted(best.values(), key=lambda x: x[1]):
            doc = metadata[idx]
            rid = doc.get("id")
            row = session.execute(
                text("SELECT id, title, ingredients, content FROM recipe_new WHERE id=:id"),
                {"id": rid}
            ).fetchone()
            if not row or row.title in seen:
                continue
            seen.add(row.title)
            recipe_ing_data = RECIPE_INGREDIENT_MAP.get(rid, {"main": set(), "sub": set()})
            final_score, matched_main, matched_sub = calculate_weighted_score(
                user_set,
                recipe_ing_data["main"],
                recipe_ing_data["sub"],
                dist,
                main_weight=2.0
            )
            if len(matched_main) == 0 and len(matched_sub) == 0:
                continue
            content = row.content if isinstance(row.content, str) else str(row.content)
            results.append({
                "id": rid,
                "title": row.title,
                "content": content.replace("\n", " "),
                "score": final_score,
                "matched_main_count": len(matched_main),
                "matched_main_ingredients": matched_main,
                "matched_sub_ingredients": matched_sub,
            })
        results.sort(key=lambda x: (x["matched_main_count"], x["score"]), reverse=True)
        print(f"최종 추천 결과: {len(results)}개")
        return results
    finally:
        session.close()


# --- [7. 수정된 출력부: 레시피 재료 정보 포함 JSON 출력] ---
def main():
    vision_raw_text = "당근, 대파, 오렌지, 토마토, 감자, 애호박, 피망, 버섯, 오이, 콩, 식빵, 크래커, 라면, 파스타, 팝콘"
    print(f"--- 1. Vision API 결과 (raw_text) ---")
    print(f"{vision_raw_text}\n")

    try:
        ingredients_list = [item.strip() for item in vision_raw_text.split(',')]
        print(f"--- 2. RAG 입력용 재료 리스트 ---")
        print(f"{ingredients_list}\n")
    except Exception as e:
        print(f"🚨 [오류] raw_text 파싱 실패: {e}")
        sys.exit(1)

    print(f"--- 3. RAG (FAISS + DB + DB 가중치) 검색 시작... ---")
    try:
        ranked_recipes = recommend_recipes_new_table(user_ingredients=ingredients_list, top_k=5)
        print("✅ RAG (FAISS + DB) 검색 성공.")
        print("--- 4. [최종 성공] RAG 검색 결과 (Top 5 JSON with ingredients) ---")

        if not ranked_recipes:
            print("매칭되는 레시피가 없습니다.")
            sys.exit(0)

        final_json_response = {}

        for i, recipe in enumerate(ranked_recipes[:5]):
            rank_key = str(i + 1)

            # --- ✅ DB에서 불러온 레시피 코드 기반으로 재료 조회 ---
            rid = recipe.get("id")
            recipe_ing_data = RECIPE_INGREDIENT_MAP.get(rid, {"main": set(), "sub": set()})

            main_ing = sorted(list(recipe_ing_data["main"]))
            sub_ing = sorted(list(recipe_ing_data["sub"]))
            all_ing = sorted(list(recipe_ing_data["main"].union(recipe_ing_data["sub"])))

            # --- ✅ recipe_details에 재료 정보 추가 ---
            recipe["main_ingredients"] = main_ing
            recipe["sub_ingredients"] = sub_ing
            recipe["all_ingredients"] = all_ing

            # --- ✅ JSON 출력 구조 ---
            final_json_response[rank_key] = {
                "score_info": f"(Score: {recipe.get('score'):.4f})",
                "matched_main_ingredients": recipe.get("matched_main_ingredients"),
                "matched_sub_ingredients": recipe.get("matched_sub_ingredients"),
                "recipe_details": recipe
            }

        # 보기 좋게 출력
        import pprint
        pprint.pprint(final_json_response)

    except Exception as e:
        print(f"🚨 [오류] RAG 검색 중 오류 발생:")
        traceback.print_exc()
        print(f"\nDB가 '{DB_HOST}:{DB_PORT}'에서 접근 가능한지 확인하세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
