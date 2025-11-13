import faiss, pickle, numpy as np, math
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from app.db import SessionLocal
import re

INDEX_SAVE_PATH = "faiss_store/index.faiss"
META_SAVE_PATH  = "faiss_store/metadata.pkl"

# 모델·인덱스 한 번만 로딩 (Apple Silicon M1 대응 - CPU 사용)
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
index = faiss.read_index(INDEX_SAVE_PATH)
with open(META_SAVE_PATH, "rb") as f:
    metadata = pickle.load(f)

# 동의어/유의어 사전
SYNONYM_MAP = {
    # 계란 관련
    "계란": "달걀",
    "달걀": "달걀",
    "노른자": "달걀",
    "흰자": "달걀",
    
    # 간장 관련
    "진간장": "간장",
    "양조간장": "간장",
    "간장": "간장",
    "국간장": "간장",
    
    # 설탕 관련
    "설탕": "설탕",
    "흑설탕": "설탕",
    "백설탕": "설탕",
    "황설탕": "설탕",
    
    # 식용유 관련
    "식용유": "식용유",
    "카놀라유": "식용유",
    "포도씨유": "식용유",
    "올리브유": "식용유",
    
    # 파 관련
    "대파": "파",
    "쪽파": "파",
    "파": "파",
    "실파": "파",
    "청파": "파",
    
    # 양파 관련
    "양파": "양파",
    "적양파": "양파",
    "흰양파": "양파",
    
    # 감자 관련
    "감자": "감자",
    "새감자": "감자",
    "조리감자": "감자",
    
    # 당근 관련
    "당근": "당근",
    "홍당근": "당근",
    
    # 소금 관련
    "소금": "소금",
    "천일염": "소금",
    "굵은소금": "소금",
    
    # 후추 관련
    "후추": "후추",
    "흑후추": "후추",
    "백후추": "후추",
    
    # 마늘 관련
    "마늘": "마늘",
    "다진마늘": "마늘",
    "편마늘": "마늘",
    
    # 고추장 관련
    "고추장": "고추장",
    "참고추장": "고추장",
    
    # 고춧가루 관련
    "고춧가루": "고춧가루",
    "매운고춧가루": "고춧가루",
    "순한고춧가루": "고춧가루",
    
    # 참기름 관련
    "참기름": "참기름",
    "들기름": "참기름",
    
    # 버터 관련
    "버터": "버터",
    "무염버터": "버터",
    "유산지": "버터",
    
    # 물 관련
    "물": "물",
    "차가운": "물",
    "따뜻한": "물",
    "미지근한": "물",
}

def extract_name(ingredient):
    # 한글, 영문만 남기고 나머지(숫자, 특수문자, 단위 등) 제거
    cleaned = re.sub(r'[^가-힣a-zA-Z]', '', ingredient)
    
    # 접두어 제거 (진, 생, 말린, 건, 등)
    prefixes = ['진', '생', '말린', '건', '다진', '채썬', '썰은', '썬', '새', '조리', '참', '매운', '순한', '흰', '적', '홍']
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    # 동의어 통일
    return SYNONYM_MAP.get(cleaned, cleaned) if cleaned else ingredient

def recommend_recipes(user_ingredients: list, top_k: int = 500):
    print(f"\n=== 검색 시작: {user_ingredients} ===")
    
    query = f"이 요리의 재료는 {', '.join(user_ingredients)}입니다."
    emb = model.encode([query]).astype("float32")
    D, I = index.search(emb, top_k)
    
    print(f"\nFAISS 검색 결과: {len(I[0])}개")
    print(f"첫 5개 거리값: {D[0][:5]}")

    with SessionLocal() as session:
        best = {}
        for idx, dist in zip(I[0], D[0]):
            if idx < len(metadata):
                rid = metadata[idx].get("id")
                if rid and (rid not in best or dist < best[rid][1]):
                    best[rid] = (idx, dist)

        print(f"\n중복 제거 후 레시피 수: {len(best)}")

        results = []
        seen = set()
        user_clean = [extract_name(i) for i in user_ingredients]
        print(f"\n정제된 사용자 재료: {user_clean}")

        for idx, dist in sorted(best.values(), key=lambda x: x[1]):
            doc = metadata[idx]
            raw = doc.get("ingredients", "").replace(" ", "")
            recipe_clean = [extract_name(i) for i in filter(None, raw.split(","))]
            
            if len(results) < 5:  # 처음 5개만 로그 출력
                print(f"\n레시피: {doc.get('title')}")
                print(f"원본 재료: {raw}")
                print(f"정제된 재료: {recipe_clean}")

            # 부분 포함 매칭: 입력 재료가 레시피 재료의 부분 문자열로 포함되어 있으면 매칭 인정
            matched = []
            for u in user_clean:
                for r in recipe_clean:
                    if u and r and (u in r or r in u):
                        matched.append(u)
                        break

            if not matched:
                continue

            # 매칭 점수 계산 방식 변경
            match_score = len(matched) / len(user_clean)  # 사용자 재료 중 매칭된 비율
            dist_score = 1 / (1 + dist)
            final_score = 0.3 * dist_score + 0.7 * match_score  # 매칭 점수 비중 증가

            if match_score < 0.1:  # 임계값을 0.1로 낮춤 (10% 이상 매칭)
                continue

            rid = doc.get("id")
            row = session.execute(
                text("SELECT id, title, ingredients, content FROM recipe WHERE id=:id"),
                {"id": rid}
            ).fetchone()
            if not row or row.title in seen:
                continue
            seen.add(row.title)

            content = row.content if isinstance(row.content, str) else str(row.content)
            results.append({
                "title": row.title,
                "ingredients": row.ingredients,
                "content": content.replace("\n", " "),
                "match_score": match_score,
                "matched_ingredients": matched
            })

        # 매칭된 재료 수를 우선적으로 고려하여 정렬
        results.sort(key=lambda x: (len(x["matched_ingredients"]), x["match_score"]), reverse=True)
        
        print(f"\n최종 추천 결과: {len(results)}개")
        return results