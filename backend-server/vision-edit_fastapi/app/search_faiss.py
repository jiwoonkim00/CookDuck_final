# app/faiss_search.py

import faiss, pickle, numpy as np, math
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from app.db import SessionLocal

INDEX_SAVE_PATH = "faiss_store/index.faiss"
META_SAVE_PATH  = "faiss_store/metadata.pkl"

# 모델·인덱스 한 번만 로딩 (Apple Silicon M1 대응 - CPU 사용)
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
index = faiss.read_index(INDEX_SAVE_PATH)
with open(META_SAVE_PATH, "rb") as f:
    metadata = pickle.load(f)

def recommend_recipes(user_ingredients: list, top_k: int = 100):
    # 1) 쿼리 임베딩
    query = f"요리에 사용된 재료는 {', '.join(user_ingredients)}입니다."
    emb = model.encode([query]).astype("float32")

    # 2) FAISS 검색
    D, I = index.search(emb, top_k)

    with SessionLocal() as session:
        # 3) 중복·거리 처리
        best = {}
        for idx, dist in zip(I[0], D[0]):
            if idx < len(metadata):
                rid = metadata[idx].get("id")
                if rid and (rid not in best or dist < best[rid][1]):
                    best[rid] = (idx, dist)

        # 4) 정렬 후 필터링
        results = []
        seen = set()
        user_set = set(user_ingredients)
        for idx, dist in sorted(best.values(), key=lambda x: x[1]):
            doc = metadata[idx]
            raw = doc.get("ingredients","").replace(" ","")
            recipe_set = set(filter(None, raw.split(",")))

            common = list(user_set & recipe_set)
            match_score = len(common) / (len(recipe_set) or 1)
            dist_score  = 1/(1+dist)
            final_score = 1.0 if match_score==1.0 else 0.4*dist_score+0.6*match_score

            if match_score < 0.3:  # 30% 이하 거르기
                continue

            rid = doc.get("id")
            row = session.execute(
                text("SELECT id, title, ingredients, content FROM recipe WHERE id=:id"),
                {"id": rid}
            ).fetchone()
            if not row or row.title in seen:
                continue
            seen.add(row.title)

            content = row.content if isinstance(row.content,str) else str(row.content)
            results.append({
                "title":           row.title,
                "ingredients":     row.ingredients,
                "content":         content.replace("\n"," "),
            })
    return results