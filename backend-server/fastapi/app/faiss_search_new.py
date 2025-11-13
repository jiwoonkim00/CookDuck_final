"""
recipe_new 테이블용 주재료/부재료 가중치 기반 추천 시스템
"""

import faiss, pickle, numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from app.db import SessionLocal
import os
import re
from typing import List, Dict, Tuple

# 경로 설정: 컨테이너 내부 또는 로컬 실행 모두 지원
def get_faiss_path(filename: str) -> str:
    """FAISS 파일 경로 찾기"""
    # 가능한 경로들
    possible_paths = [
        f"/app/faiss_store/{filename}",  # Docker 컨테이너 내부
        f"faiss_store/{filename}",        # 로컬 실행 (현재 디렉토리)
        f"./faiss_store/{filename}",     # 로컬 실행 (명시적)
        f"../faiss_store/{filename}",    # app 폴더에서 실행 시
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 기본 경로 반환 (존재하지 않으면 나중에 에러 발생)
    return f"faiss_store/{filename}"

INDEX_SAVE_PATH = get_faiss_path("index_new.faiss")
META_SAVE_PATH = get_faiss_path("metadata_new.pkl")

# 모델·인덱스 로드
try:
    model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
    index = faiss.read_index(INDEX_SAVE_PATH)
    with open(META_SAVE_PATH, "rb") as f:
        metadata = pickle.load(f)
    print(f"✅ recipe_new 테이블용 FAISS 인덱스 로드 완료 (경로: {INDEX_SAVE_PATH})")
except Exception as e:
    print(f"⚠️ recipe_new 인덱스 로드 실패: {e}")
    print(f"   시도한 경로: {INDEX_SAVE_PATH}")
    print("💡 먼저 build_faiss_new_table.py를 실행하여 인덱스를 구축하세요.")
    index = None
    metadata = []

# 동의어 사전
SYNONYM_MAP = {
    "계란": "달걀", "달걀": "달걀", "진간장": "간장", "간장": "간장",
    "설탕": "설탕", "백설탕": "설탕", "식용유": "식용유", "카놀라유": "식용유",
    "대파": "파", "쪽파": "파", "파": "파", "양파": "양파",
    "감자": "감자", "당근": "당근", "소금": "소금", "후추": "후추",
    "마늘": "마늘", "다진마늘": "마늘", "고추장": "고추장",
    "고춧가루": "고춧가루", "참기름": "참기름", "버터": "버터",
}

def extract_name(ingredient: str) -> str:
    """재료명 정제"""
    cleaned = re.sub(r'[^가-힣a-zA-Z]', '', str(ingredient))
    prefixes = ['진', '생', '말린', '건', '다진', '채썬', '썰은', '썬', '새', '조리']
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return SYNONYM_MAP.get(cleaned, cleaned) if cleaned else ingredient

def calculate_weighted_score(
    user_main: List[str],
    user_sub: List[str],
    recipe_main: List[str],
    recipe_sub: List[str],
    distance: float,
    main_weight: float = 2.0,
    sub_weight: float = 1.0
) -> Tuple[float, float, List[str], List[str]]:
    """주재료/부재료 가중치를 적용한 매칭 점수 계산"""
    
    # 주재료 매칭
    matched_main = []
    user_main_clean = [extract_name(ing) for ing in user_main]
    recipe_main_clean = [extract_name(ing) for ing in recipe_main]
    
    for u_ing in user_main_clean:
        for r_ing in recipe_main_clean:
            if u_ing and r_ing and (u_ing in r_ing or r_ing in u_ing):
                matched_main.append(u_ing)
                break
    
    # 부재료 매칭
    matched_sub = []
    user_sub_clean = [extract_name(ing) for ing in user_sub]
    recipe_sub_clean = [extract_name(ing) for ing in recipe_sub]
    
    for u_ing in user_sub_clean:
        for r_ing in recipe_sub_clean:
            if u_ing and r_ing and (u_ing in r_ing or r_ing in u_ing):
                matched_sub.append(u_ing)
                break
    
    # 가중치 적용 점수 계산
    total_user_ingredients = len(user_main) + len(user_sub)
    if total_user_ingredients == 0:
        return 0.0, 0.0, [], []
    
    # 주재료 점수 (가중치 적용)
    main_score = (len(matched_main) / len(user_main)) * main_weight if user_main else 0.0
    
    # 부재료 점수
    sub_score = (len(matched_sub) / len(user_sub)) * sub_weight if user_sub else 0.0
    
    # 정규화된 매칭 점수
    weighted_match_score = (main_score + sub_score) / (main_weight + sub_weight)
    
    # 전체 매칭 비율
    total_matched = len(matched_main) + len(matched_sub)
    simple_match_score = total_matched / total_user_ingredients if total_user_ingredients > 0 else 0.0
    
    # 거리 점수
    dist_score = 1 / (1 + distance)
    
    # 최종 점수
    if matched_main:
        final_score = 0.2 * dist_score + 0.8 * weighted_match_score
    else:
        final_score = 0.4 * dist_score + 0.6 * simple_match_score
    
    return final_score, weighted_match_score, matched_main, matched_sub

def recommend_recipes_new_table(
    user_ingredients: List[str],
    user_main_ingredients: List[str] = None,
    user_sub_ingredients: List[str] = None,
    top_k: int = 500,
    main_weight: float = 2.0
) -> List[Dict]:
    """
    recipe_new 테이블 기반 주재료/부재료 가중치 추천
    """
    if index is None:
        raise Exception("FAISS 인덱스가 로드되지 않았습니다. build_faiss_new_table.py를 실행하세요.")
    
    print(f"\n=== recipe_new 테이블 추천 시작 ===")
    print(f"사용자 재료: {user_ingredients}")
    
    # 주재료/부재료 자동 분류
    if user_main_ingredients is None or user_sub_ingredients is None:
        user_main_ingredients, user_sub_ingredients = classify_user_ingredients(user_ingredients)
    
    print(f"주재료: {user_main_ingredients}")
    print(f"부재료: {user_sub_ingredients}")
    
    # 쿼리 임베딩 (주재료 강조)
    main_text = ", ".join(user_main_ingredients) if user_main_ingredients else ""
    query = f"이 요리의 주재료는 {main_text}입니다."
    if user_sub_ingredients:
        query += f" 부재료는 {', '.join(user_sub_ingredients)}입니다."
    
    emb = model.encode([query]).astype("float32")
    D, I = index.search(emb, top_k)
    
    print(f"FAISS 검색 결과: {len(I[0])}개")
    
    # 로컬 실행 시 DB 연결 설정
    try:
        # Docker 컨테이너 내부에서 실행되는 경우
        session = SessionLocal()
    except Exception as e:
        # 로컬 실행 시 직접 DB 연결 생성
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT = os.getenv("DB_PORT", "3307")
        DB_URL = f"mysql+pymysql://root:root@{DB_HOST}:{DB_PORT}/recipe_db"
        local_engine = create_engine(DB_URL)
        LocalSession = sessionmaker(bind=local_engine)
        session = LocalSession()
    
    try:
        best = {}
        for idx, dist in zip(I[0], D[0]):
            if idx < len(metadata):
                rid = metadata[idx].get("id")
                if rid and (rid not in best or dist < best[rid][1]):
                    best[rid] = (idx, dist)
        
        print(f"중복 제거 후 레시피 수: {len(best)}")
        
        results = []
        seen = set()
        
        for idx, dist in sorted(best.values(), key=lambda x: x[1]):
            doc = metadata[idx]
            rid = doc.get("id")
            
            # recipe_new 테이블에서 데이터 조회
            row = session.execute(
                text("""
                    SELECT id, title, ingredients, content, 
                           main_ingredients, sub_ingredients 
                    FROM recipe_new
                    WHERE id=:id
                """),
                {"id": rid}
            ).fetchone()
            
            if not row or row.title in seen:
                continue
            seen.add(row.title)
            
            # 주재료/부재료 파싱
            recipe_main = []
            recipe_sub = []
            
            if row.main_ingredients:
                recipe_main = [extract_name(ing.strip()) 
                             for ing in str(row.main_ingredients).split(",") if ing.strip()]
            if row.sub_ingredients:
                recipe_sub = [extract_name(ing.strip()) 
                             for ing in str(row.sub_ingredients).split(",") if ing.strip()]
            
            # 주재료/부재료 정보가 없으면 전체 재료에서 추론
            if not recipe_main and not recipe_sub and row.ingredients:
                all_ingredients = [extract_name(ing.strip()) 
                                 for ing in str(row.ingredients).split(",") if ing.strip()]
                sub_keywords = ['소금', '설탕', '간장', '식용유', '물', '후추', '마늘', '파']
                for ing in all_ingredients:
                    if any(kw in ing for kw in sub_keywords):
                        recipe_sub.append(ing)
                    else:
                        recipe_main.append(ing)
            
            # 가중치 적용 점수 계산
            final_score, match_score, matched_main, matched_sub = calculate_weighted_score(
                user_main_ingredients,
                user_sub_ingredients,
                recipe_main,
                recipe_sub,
                dist,
                main_weight
            )
            
            # 최소 매칭 기준
            if not matched_main and len(user_main_ingredients) > 0:
                if match_score < 0.2:
                    continue
            
            if match_score < 0.1:
                continue
            
            content = row.content if isinstance(row.content, str) else str(row.content)
            results.append({
                "id": rid,
                "title": row.title,
                "ingredients": row.ingredients,
                "main_ingredients": ",".join(recipe_main) if recipe_main else "",
                "sub_ingredients": ",".join(recipe_sub) if recipe_sub else "",
                "content": content.replace("\n", " "),
                "score": final_score,
                "match_score": match_score,
                "matched_main_ingredients": matched_main,
                "matched_sub_ingredients": matched_sub,
                "matched_ingredients": matched_main + matched_sub,
                "distance": float(dist)
            })
        
        # 정렬: 주재료 매칭 수 > 최종 점수
        results.sort(
            key=lambda x: (
                len(x["matched_main_ingredients"]),
                x["score"]
            ),
            reverse=True
        )
        
        print(f"최종 추천 결과: {len(results)}개")
        return results
    finally:
        session.close()

def classify_user_ingredients(ingredients: List[str]) -> Tuple[List[str], List[str]]:
    """사용자 입력 재료를 주재료/부재료로 자동 분류"""
    main = []
    sub = []
    
    sub_keywords = [
        '소금', '설탕', '후추', '간장', '된장', '고추장', '식초', '참기름',
        '식용유', '물', '마늘', '파', '양파'
    ]
    
    for ing in ingredients:
        cleaned = extract_name(ing)
        is_sub = any(keyword in cleaned for keyword in sub_keywords)
        if is_sub:
            sub.append(cleaned)
        else:
            main.append(cleaned)
    
    return main, sub

