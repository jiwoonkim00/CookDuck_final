# FAISS 경로 수정 완료

## 🔧 수정 사항

두 개의 `faiss_store` 폴더가 존재하는 문제를 해결했습니다.

### 기존 문제
- `./faiss_store/` - 새 인덱스 파일 위치 (index_new.faiss, metadata_new.pkl)
- `./app/faiss_store/` - 이전 파일 위치 (metadata.pkl)

### 해결 방법

1. **faiss_search_new.py 수정**
   - `get_faiss_path()` 함수 추가
   - 여러 가능한 경로를 순차적으로 확인
   - Docker 컨테이너 내부 (`/app/faiss_store/`) 우선 확인
   - 로컬 실행 경로도 지원

2. **build_faiss_new_table.py 수정**
   - `os.path.join()` 사용하여 올바른 경로 생성
   - 작업 디렉토리 기준으로 `faiss_store` 폴더 찾기

3. **docker-compose.yml 수정**
   - 볼륨 마운트 추가: `./backend-server/fastapi/faiss_store:/app/faiss_store`
   - 컨테이너 내부에서 `/app/faiss_store/`로 접근

## ✅ 확인 결과

- 인덱스 경로: `/app/faiss_store/index_new.faiss` ✅
- 메타데이터 경로: `/app/faiss_store/metadata_new.pkl` ✅
- 파일 존재 확인: 모두 True ✅

## 📁 현재 구조

```
backend-server/fastapi/
├── faiss_store/              # 메인 FAISS 저장소 (볼륨 마운트)
│   ├── index.faiss          # 기존 인덱스 (24만개)
│   ├── index_new.faiss      # 새 인덱스 (537개) ✅
│   ├── metadata.pkl         # 기존 메타데이터
│   └── metadata_new.pkl     # 새 메타데이터 ✅
└── app/
    └── faiss_store/         # (사용 안 함, 레거시)
```

## 🔍 경로 확인 함수

`faiss_search_new.py`의 `get_faiss_path()` 함수는 다음 순서로 경로를 확인합니다:

1. `/app/faiss_store/{filename}` - Docker 컨테이너 내부
2. `faiss_store/{filename}` - 로컬 실행 (현재 디렉토리)
3. `./faiss_store/{filename}` - 로컬 실행 (명시적)
4. `../faiss_store/{filename}` - app 폴더에서 실행 시

첫 번째로 존재하는 경로를 사용합니다.

