"""
recipe_new 테이블에서 데이터를 읽어서 FAISS 인덱스를 구축하는 스크립트
주재료를 강조한 임베딩 생성
"""

import logging
import faiss
import numpy as np
from app.db import SessionLocal
from sentence_transformers import SentenceTransformer
import os
import pickle
from tqdm import tqdm
import torch
import gc
from sqlalchemy import text

# 설정
CHUNK_SIZE = 1000
# 경로 설정: 작업 디렉토리 기준으로 faiss_store 폴더 사용
FAISS_STORE_DIR = "faiss_store"
if not os.path.exists(FAISS_STORE_DIR):
    # app 폴더에서 실행하는 경우
    FAISS_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_store") if "__file__" in globals() else "faiss_store"

INDEX_SAVE_PATH = os.path.join(FAISS_STORE_DIR, "index_new.faiss")
META_SAVE_PATH = os.path.join(FAISS_STORE_DIR, "metadata_new.pkl")
LAST_PROCESSED_PATH = os.path.join(FAISS_STORE_DIR, "last_processed_new.txt")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 모델 로드
logger.info("📦 SentenceTransformer 모델 로딩 중...")
try:
    # M1 Mac 지원 (CPU/MPS)
    device = "cpu"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    
    model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device=device)
    dimension = model.get_sentence_embedding_dimension()
    logger.info(f"✅ 모델 로딩 완료 (device: {device}, dimension: {dimension})")
except Exception as e:
    logger.error(f"❌ 모델 로딩 실패: {e}")
    raise

# FAISS 저장 폴더 초기화
if not os.path.exists(FAISS_STORE_DIR):
    os.makedirs(FAISS_STORE_DIR)

# 기존 인덱스 확인
if os.path.exists(INDEX_SAVE_PATH) and os.path.exists(META_SAVE_PATH):
    logger.warning("⚠️  기존 인덱스 파일이 있습니다.")
    response = input("기존 인덱스를 덮어쓰시겠습니까? (y/N): ")
    if response.lower() != 'y':
        logger.info("작업 취소됨")
        exit(0)
    # 기존 파일 삭제
    for path in [INDEX_SAVE_PATH, META_SAVE_PATH, LAST_PROCESSED_PATH]:
        if os.path.exists(path):
            os.remove(path)

try:
    # 데이터 연결 및 로딩
    logger.info("🔌 DB 연결 중...")
    # 로컬 실행 시에는 직접 DB 연결 생성
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 로컬 실행용 DB URL (Docker 컨테이너 내부가 아닌 경우)
    import os
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3307")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "root")
    DB_NAME = os.getenv("DB_NAME", "recipe_db")
    
    DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    local_engine = create_engine(DB_URL)
    LocalSession = sessionmaker(bind=local_engine)
    session = LocalSession()
    
    # recipe_new 테이블에서 데이터 로드
    result = session.execute(text("""
        SELECT id, title, ingredients, tools, content, main_ingredients, sub_ingredients 
        FROM recipe_new
        ORDER BY id
    """))
    data = result.fetchall()
    logger.info(f"✅ 총 {len(data)}개 레시피 로딩 완료")
    
    if len(data) == 0:
        logger.error("❌ recipe_new 테이블에 데이터가 없습니다.")
        logger.info("💡 먼저 load_csv_to_new_table.py를 실행하여 데이터를 로드하세요.")
        session.close()
        exit(1)
    
    # 텍스트 변환 함수 (주재료 강조)
    def recipe_to_text(row):
        """레시피를 임베딩용 텍스트로 변환 (주재료 강조)"""
        title = str(row.title) if row.title else ""
        
        # 주재료가 있으면 주재료를 강조한 텍스트 생성
        if row.main_ingredients:
            main_list = str(row.main_ingredients).split(",")
            main_list = [m.strip() for m in main_list if m.strip()][:3]  # 상위 3개 주재료만
            if main_list:
                return f"{title} 레시피의 주재료는 {', '.join(main_list)}입니다."
        
        # 주재료가 없으면 기존 방식
        if row.ingredients:
            ingredients = str(row.ingredients).split(",")[:5]  # 상위 5개 재료
            ingredients = [i.strip() for i in ingredients if i.strip()]
            if ingredients:
                return f"{title} 레시피의 재료는 {', '.join(ingredients)}입니다."
        
        # 재료 정보가 없으면 제목만
        return f"{title} 레시피입니다."
    
    texts = [recipe_to_text(row) for row in data]
    
    # 메타데이터 초기화
    metadata = []
    
    # 처리 지점 로드
    if os.path.exists(LAST_PROCESSED_PATH):
        with open(LAST_PROCESSED_PATH, "r") as f:
            last_processed = int(f.read().strip() or 0)
    else:
        last_processed = 0
    
    # 인덱스 초기화
    logger.info("📁 새로운 FAISS 인덱스 생성")
    index = faiss.IndexFlatL2(dimension)
    
    # 벡터화 및 저장 루프
    logger.info(f"🧠 임베딩 시작 (처리 지점: {last_processed})...")
    
    for start in tqdm(range(last_processed, len(texts), CHUNK_SIZE), desc="임베딩 진행"):
        end = min(start + CHUNK_SIZE, len(texts))
        text_chunk = texts[start:end]
        
        filtered_texts = []
        filtered_ids = []
        
        for i, text in enumerate(text_chunk):
            if isinstance(text, str) and len(text.strip()) > 0:
                filtered_texts.append(text)
                row = data[start + i]
                filtered_ids.append({
                    "id": row.id,
                    "title": row.title,
                    "ingredients": row.ingredients,
                    "main_ingredients": row.main_ingredients,
                    "sub_ingredients": row.sub_ingredients,
                    "content": row.content
                })
        
        if not filtered_texts:
            continue
        
        logger.info(f"🧠 임베딩 중: {start} ~ {end} (총 {len(filtered_texts)}개)")
        
        try:
            # 메모리 정리
            gc.collect()
            
            emb_chunk = model.encode(filtered_texts, show_progress_bar=False)
            
            if emb_chunk.ndim != 2 or emb_chunk.shape[1] != dimension:
                logger.error(f"❌ 잘못된 벡터 차원: {emb_chunk.shape}")
                continue
            
            index.add(np.array(emb_chunk).astype("float32"))
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
            
            logger.info(f"✅ {end}/{len(texts)} 완료 (인덱스 크기: {index.ntotal})")
            
        except Exception as e:
            logger.exception(f"❌ 오류 발생: {start}-{end} 구간 → {str(e)}")
            break
    
    logger.info("=" * 60)
    logger.info("✅ 전체 임베딩 및 저장 완료!")
    logger.info(f"📊 인덱스 크기: {index.ntotal}개")
    logger.info(f"💾 저장 경로:")
    logger.info(f"   - 인덱스: {INDEX_SAVE_PATH}")
    logger.info(f"   - 메타데이터: {META_SAVE_PATH}")
    logger.info("=" * 60)

except Exception as e:
    logger.exception(f"❌ 치명적 오류 발생: {str(e)}")
    raise

finally:
    # 세션 종료
    if 'session' in locals():
        session.close()
    logger.info("🔌 데이터베이스 연결 종료")

