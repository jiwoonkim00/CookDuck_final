import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from app.db import SessionLocal
import math
from sqlalchemy import text # session.execute를 계속 사용하려면 필요


INDEX_SAVE_PATH = "faiss_store/index.faiss"
META_SAVE_PATH = "faiss_store/metadata.pkl"

def recipe_to_text(row):
    # row가 딕셔너리가 아닌 다른 형태일 경우에 대비하여 .get() 사용
    title = row.get('title', '제목 없음')
    ingredients = row.get('ingredients', '재료 없음')
    return f"{title} 레시피의 주요 재료는 {ingredients}입니다. 이 조합은 풍부한 맛을 내는 데 중요한 역할을 합니다."

# 모델 로딩 (Apple Silicon M1 대응 - CPU 사용)
try:
    model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
    # dimension = model.get_sentence_embedding_dimension() # 현재 사용되지 않으므로 제거 가능
    index = faiss.read_index(INDEX_SAVE_PATH)
    with open(META_SAVE_PATH, "rb") as f:
        metadata = pickle.load(f)
    print("✅ 모델, FAISS 인덱스 및 메타데이터 로딩 완료.")
except Exception as e:
    print(f"❌ 초기 로딩 중 에러 발생: {e}")
    print("FAISS 인덱스 파일 또는 메타데이터 파일 경로를 확인하거나, 파일이 손상되지 않았는지 확인하세요.")
    exit(1) # 에러 발생 시 스크립트 종료

# 사용자 입력 임베딩
user_ingredients = ["고추장","계란","김치"]
query_sentence = f"요리에 사용된 재료는 {', '.join(user_ingredients)}입니다."
query_embedding = model.encode([query_sentence]).astype("float32") # reshape 제거, astype은 유지

# 유사한 벡터 20개 검색
k = 100
D, I = index.search(query_embedding, k) # np.array(query_embedding) 불필요

# DB 연결
# with 문을 사용하여 세션 자동 관리
with SessionLocal() as session: # 이 부분 추가
    print(f"\n📌 입력한 재료로 만들 수 있는 요리 추천 결과입니다! ({', '.join(user_ingredients)})")
    result_found = False  # 결과 유무 플래그

    seen_titles = set()

    # 중복 제거 (레시피 ID 기준) + distance도 같이 관리
    recipe_best_result = {}

    for idx, distance in zip(I[0], D[0]):
        if idx < len(metadata):
            doc = metadata[idx]
            recipe_id = doc.get("id")
            # 같은 recipe_id 중에서는 distance가 더 작은 것(= 더 유사한 것)만 저장
            if recipe_id is not None: # recipe_id가 None이 아닌지 확인
                if (recipe_id not in recipe_best_result) or (distance < recipe_best_result[recipe_id][1]):
                    recipe_best_result[recipe_id] = (idx, distance)

    # 정리된 결과
    unique_results = list(recipe_best_result.values())

    # 중복 제거된 결과 출력 및 정렬
    sorted_results = sorted(unique_results, key=lambda x: x[1]) # 거리 기준으로 정렬
    for idx, distance in sorted_results:
        if idx >= len(metadata):
            continue  # 방어: FAISS 인덱스가 메타데이터보다 클 경우
        try:
            doc = metadata[idx]
            recipe_ingredients_str = doc.get("ingredients", "").replace(" ", "")
            recipe_ingredients = set(filter(None, recipe_ingredients_str.split(","))) # 빈 문자열 필터링
            user_ingredient_set = set(user_ingredients)
            
            # 재료 일치율 계산
            common_ingredients = user_ingredient_set.intersection(recipe_ingredients)
            match_score = len(common_ingredients) / (len(recipe_ingredients) or 1) # 0으로 나누는 것 방지

            distance_score = 1 / (1 + distance)  # 거리 기반 유사도 변환
            
            if match_score == 1.0:
                final_score = 1.0
            else:
                final_score = 0.4 * distance_score + 0.6 * match_score  # 재료 일치 비중 강화

            if match_score >= 0.3:  # 재료 30% 이상 매칭 필터링
                recipe_id = doc.get("id") # metadata[idx]["id"] 대신 .get() 사용
                if recipe_id is not None:
                    # SQLAlchemy text() 사용하여 쿼리
                    stmt = text("SELECT title, ingredients, content FROM recipe WHERE id = :id")
                    recipe = session.execute(stmt, {"id": recipe_id}).fetchone()
                    if recipe and recipe.title not in seen_titles:
                        seen_titles.add(recipe.title)
                        
                        content_full = recipe.content # 자르지 않고 전체 내용을 가져옵니다.
                        if not isinstance(content_full, str):
                            content_full = str(content_full)
                        content_full_formatted = content_full.replace('\n', ' ') # 줄바꿈만 공백으로 변경

                        print(f"\n--- 레시피 ID: {recipe_id} (최종 점수: {final_score:.2f}, 재료 매칭: {match_score:.2f}) ---")
                        print(f"🍽️ 제목: {recipe.title}")
                        print(f"🥬 재료: {recipe.ingredients}")
                        print(f"✅ 일치하는 재료: {', '.join(common_ingredients) if common_ingredients else '없음'}")
                        print(f"📖 내용: {content_full_formatted}") # 수정된 부분: 자르지 않은 전체 내용 출력
                        result_found = True
        except Exception as e:
            print(f"❗ 예외 발생 (metadata index={idx}, recipe_id={doc.get('id', 'N/A')}): {e}")
            continue

    if not result_found:
        print("❗ 검색된 결과가 없습니다. 유사도 조건이나 입력 재료를 조정해보세요.")

# 세션은 with 문을 사용했으므로 여기서 session.close()는 필요 없습니다.