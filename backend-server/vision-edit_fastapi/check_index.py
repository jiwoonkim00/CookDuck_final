#!/usr/bin/env python3
"""FAISS 인덱스 검증 스크립트"""

import faiss
import pickle
import sys

INDEX_PATH = "faiss_store/index_new.faiss"
META_PATH = "faiss_store/metadata_new.pkl"

print("=" * 60)
print("📊 FAISS 인덱스 검증")
print("=" * 60)

try:
    # 인덱스 로드
    print("\n1️⃣ 인덱스 파일 확인...")
    index = faiss.read_index(INDEX_PATH)
    print(f"   ✅ 인덱스 크기: {index.ntotal}개 벡터")
    print(f"   ✅ 벡터 차원: {index.d}")
    
    # 메타데이터 로드
    print("\n2️⃣ 메타데이터 파일 확인...")
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)
    print(f"   ✅ 메타데이터 크기: {len(metadata)}개")
    
    # 크기 일치 확인
    if index.ntotal == len(metadata):
        print(f"   ✅ 인덱스와 메타데이터 크기 일치!")
    else:
        print(f"   ⚠️  크기 불일치: 인덱스={index.ntotal}, 메타데이터={len(metadata)}")
    
    # 샘플 데이터 확인
    print("\n3️⃣ 샘플 데이터 확인...")
    if metadata:
        sample = metadata[0]
        print(f"   첫 번째 레시피:")
        print(f"   - ID: {sample.get('id', 'N/A')}")
        print(f"   - 제목: {sample.get('title', 'N/A')}")
        print(f"   - 주재료: {sample.get('main_ingredients', 'N/A')}")
        print(f"   - 부재료: {sample.get('sub_ingredients', 'N/A')}")
    
    # 통계
    print("\n4️⃣ 통계...")
    with_main = sum(1 for m in metadata if m.get('main_ingredients'))
    with_sub = sum(1 for m in metadata if m.get('sub_ingredients'))
    print(f"   주재료 정보 있음: {with_main}개 ({with_main*100//len(metadata)}%)")
    print(f"   부재료 정보 있음: {with_sub}개 ({with_sub*100//len(metadata)}%)")
    
    print("\n" + "=" * 60)
    print("✅ 인덱스 검증 완료!")
    print("=" * 60)
    
except FileNotFoundError as e:
    print(f"❌ 파일을 찾을 수 없습니다: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

