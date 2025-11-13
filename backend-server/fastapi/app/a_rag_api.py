# ================================================================
# 파일 이름: rag_api.py
# 위치: /Users/server/Desktop/cookduck_backup/backend-server/fastapi/app/
# 역할: RAG 레시피 검색을 '/rag_recipe' API 엔드포인트로 제공합니다.
# ================================================================

import os
import re
import logging
import pickle
import traceback
from typing import List, Dict, Tuple, Set
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ================================================================
# [1] 환경 설정 (세그폴트 방지)
# ================================================================
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")

# ================================================================
# [2] .env 파일 로드
# ================================================================
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ (rag_api) .env 파일 로드 성공: {dotenv_path}")
else:
    print(f"🚨 (rag_api) [경고] .env 파일을 찾을 수 없습니다: {dotenv_path}")

# ================================================================
# [3] FAISS 인덱스 및 메타데이터 로드
# ================================================================
def get_faiss_path(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_store", filename)
    if os.path.exists(path):
        return path
    raise FileNotFoundError(f"FAISS 파일을 찾을 수 없습니다: {path}")

try:
    INDEX_SAVE_PATH = get_faiss_path("index_new.faiss")
    META_SAVE_PATH = get_faiss_path("metadata_new.pkl")
    model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
    index = faiss.read_index(INDEX_SAVE_PATH)
    with open(META_SAVE_PATH, "rb") as f:
        metadata = pickle.load(f)
    print(f"✅ (rag_api) FAISS 인덱스 로드 완료 (경로: {INDEX_SAVE_PATH})")
except Exception as e:
    print(f"🚨 (rag_api) [치명적 오류] FAISS 인덱스 로드 실패: {e}")
    raise e

# ================================================================
# [4] DB 연결 설정
# ================================================================
try:
    DB_HOST = os.getenv("DB_HOST", "mariadb")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME = os.getenv("DB_NAME", "recipe_db")
    DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    local_engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=local_engine, autocommit=False, autoflush=False)
    print(f"✅ (rag_api) DB 연결 엔진 생성 성공 (대상: {DB_HOST}:{DB_PORT})")
except Exception as e:
    print(f"🚨 (rag_api) [오류] DB 엔진 생성 실패: {e}")
    raise e

# ================================================================
# [5] 재료 전처리 및 동의어 처리
# ================================================================
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

# ================================================================
# [6] recipe_ingredient_cleaned 테이블 로드
# ================================================================
RECIPE_INGREDIENT_MAP = {}
try:
    print("... (rag_api) DB에서 'recipe_ingredient_cleaned' 테이블 로드 시작 ...")
    session = SessionLocal()
    query = text("SELECT recipe_code, ingredient_name, ingredient_type_name FROM recipe_ingredient_cleaned")
    result = session.execute(query)
    for row in result.fetchall():
        recipe_code = row.recipe_code
        if recipe_code not in RECIPE_INGREDIENT_MAP:
            RECIPE_INGREDIENT_MAP[recipe_code] = {"main": set(), "sub": set()}
        cleaned_name = extract_name(row.ingredient_name)
        if row.ingredient_type_name in ("주재료", "MAIN"):
            RECIPE_INGREDIENT_MAP[recipe_code]["main"].add(cleaned_name)
        else:
            RECIPE_INGREDIENT_MAP[recipe_code]["sub"].add(cleaned_name)
    session.close()
    print(f"✅ (rag_api) 재료 DB 로드 완료 (총 {len(RECIPE_INGREDIENT_MAP)}개 레시피)")
except Exception as e:
    print(f"🚨 (rag_api) [치명적 오류] 테이블 로드 실패: {e}")
    if "session" in locals() and session:
        session.close()
    raise e

# ================================================================
# [7] 점수 계산 로직 (run_rag_db.py와 동일)
# ================================================================
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

# ================================================================
# [8] RAG 추천 로직
# ================================================================
def classify_user_ingredients(ingredients: List[str]) -> Set[str]:
    return {extract_name(ing) for ing in ingredients}

def recommend_recipes_new_table(user_ingredients: List[str], top_k: int = 538) -> List[Dict]:
    if index is None:
        raise Exception("FAISS 인덱스가 로드되지 않았습니다.")
    user_set = classify_user_ingredients(user_ingredients)
    query = f"이 요리의 재료는 {', '.join(user_set)}입니다."
    emb = model.encode([query]).astype("float32")
    D, I = index.search(emb, top_k)

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
                text("SELECT * FROM recipe_new WHERE id=:id"),
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

            recipe_details = dict(row._mapping)
            recipe_details["weighted_score"] = final_score
            recipe_details["matched_main_ingredients"] = matched_main
            recipe_details["matched_sub_ingredients"] = matched_sub
            recipe_details["faiss_distance"] = float(dist)

            recipe_details["main_ingredients_list"] = sorted(recipe_ing_data["main"])
            recipe_details["sub_ingredients_list"] = sorted(recipe_ing_data["sub"])
            recipe_details["all_ingredients_list"] = sorted(
                recipe_ing_data["main"].union(recipe_ing_data["sub"])
            )

            results.append(recipe_details)
        results.sort(key=lambda x: (len(x["matched_main_ingredients"]), x["weighted_score"]), reverse=True)
        return results
    finally:
        session.close()

# ================================================================
# [9] FastAPI 엔드포인트
# ================================================================
router = APIRouter()
logger = logging.getLogger(__name__)

class RagRequest(BaseModel):
    raw_text: str
    top_k: int = 5

@router.post("/rag_recipe")
def run_rag_search(request: RagRequest) -> Dict:
    try:
        ingredients_list = [item.strip() for item in request.raw_text.split(",")]
        ranked_recipes = recommend_recipes_new_table(user_ingredients=ingredients_list, top_k=538)
        if not ranked_recipes:
            return {"success": True, "recipes": {}}

        final_json_response = {}
        for i, recipe_details in enumerate(ranked_recipes[:request.top_k]):
            rank_key = str(i + 1)
            final_json_response[rank_key] = {
                "score_info": f"(Score: {recipe_details.get('weighted_score', 0):.4f})",
                "matched_main_ingredients": recipe_details.get("matched_main_ingredients"),
                "matched_sub_ingredients": recipe_details.get("matched_sub_ingredients"),
                "recipe_details": recipe_details,
            }

        return {"success": True, "recipes": final_json_response}

    except Exception as e:
        logger.error(f"RAG 검색 API 오류: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"RAG 검색 중 오류가 발생했습니다: {e}")
