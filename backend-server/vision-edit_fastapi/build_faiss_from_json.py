import logging
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import os, pickle
from tqdm import tqdm
import torch
import gc

# 설정
CHUNK_SIZE = 1000
INDEX_SAVE_PATH = "faiss_store/index.faiss"
META_SAVE_PATH = "faiss_store/metadata.pkl"
LAST_PROCESSED_PATH = "faiss_store/last_processed.txt"
JSON_FILE_PATH = "recipes_fixed.json"

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 모델 로드 (Apple Silicon M1 대응 - CPU 사용)
logger.info("📦 SentenceTransformer 모델 로딩 중...")
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cpu")
dimension = model.get_sentence_embedding_dimension()

# FAISS 저장 폴더 초기화
if not os.path.exists(INDEX_SAVE_PATH) or not os.path.exists(META_SAVE_PATH):
    logger.warning("❗ 기존 index 또는 metadata 파일 없음 → 처음부터 시작")
    for path in [INDEX_SAVE_PATH, META_SAVE_PATH, LAST_PROCESSED_PATH]:
        if os.path.exists(path):
            os.remove(path)

try:
    # JSON 파일 로딩
    logger.info("📄 JSON 파일 로딩 중...")
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"✅ 총 {len(data)}개 레시피 로딩 완료")

    # 텍스트 변환 함수
    def recipe_to_text(recipe):
        ingredients = recipe.get('ingredients', '')
        return f"이 요리의 재료는 {ingredients}입니다."

    texts = [recipe_to_text(recipe) for recipe in data]

    # 메타데이터 초기화
    metadata = []

    # 처리 지점 로드
    if os.path.exists(LAST_PROCESSED_PATH):
        with open(LAST_PROCESSED_PATH, "r") as f:
            last_processed = int(f.read().strip() or 0)
    else:
        last_processed = 0

    # 인덱스 초기화 (CPU 버전)
    logger.info("📁 새로운 FAISS CPU 인덱스 생성")
    index = faiss.IndexFlatL2(dimension)

    # 벡터화 및 저장 루프
    for start in range(last_processed, len(texts), CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, len(texts))
        text_chunk = texts[start:end]

        filtered_texts = []
        filtered_ids = []

        for i, text in enumerate(text_chunk):
            if isinstance(text, str) and len(text.strip()) > 0:
                filtered_texts.append(text)
                recipe = data[start + i]
                filtered_ids.append({
                    "id": recipe.get("id", start + i),
                    "title": recipe.get("title", ""),
                    "ingredients": recipe.get("ingredients", ""),
                    "content": recipe.get("content", "")
                })

        logger.info(f"🧠 임베딩 중: {start} ~ {end} (총 {len(filtered_texts)}개)")

        try:
            # 메모리 정리
            gc.collect()

            emb_chunk = model.encode(filtered_texts, show_progress_bar=True)

            if emb_chunk.ndim != 2 or emb_chunk.shape[1] != dimension:
                logger.error(f"❌ 잘못된 벡터 차원: {emb_chunk.shape}")
                continue

            index.add(np.array(emb_chunk))
            metadata.extend(filtered_ids)

            # 저장
            os.makedirs(os.path.dirname(INDEX_SAVE_PATH), exist_ok=True)
            faiss.write_index(index, INDEX_SAVE_PATH)
            with open(META_SAVE_PATH, "wb") as f:
                pickle.dump(metadata, f)
            with open(LAST_PROCESSED_PATH, "w") as f:
                f.write(str(end))

            # 메모리 정리
            del emb_chunk
            gc.collect()

        except Exception as e:
            logger.exception(f"❗ 오류 발생: {start}-{end} 구간 → {str(e)}")
            break

    logger.info("✅ 전체 임베딩 및 저장 완료!")

except Exception as e:
    logger.exception(f"❗ 치명적 오류 발생: {str(e)}")
    raise

finally:
    # 메모리 정리 완료
    pass
