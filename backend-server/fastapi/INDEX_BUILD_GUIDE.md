# FAISS 인덱스 구축 가이드 (tmux 사용)

## 📋 현재 상태
- ✅ recipe_new 테이블에 **537개 레시피** 저장 완료
- ✅ 주재료 정보: 537개
- ✅ 부재료 정보: 475개
- 🔄 FAISS 인덱스 구축 필요

## 🚀 tmux로 인덱스 구축하기

### 1. tmux 세션 시작
```bash
cd /Users/keonryul/Desktop/cookduck_backup/backend-server/fastapi
tmux new -s faiss_build
```

### 2. 가상환경 활성화 (필요시)
```bash
# 가상환경이 있다면
source venv/bin/activate

# 또는 Python3 직접 사용
# python3 build_faiss_new_table.py
```

### 3. 인덱스 구축 실행
```bash
python3 build_faiss_new_table.py
```

### 4. tmux 세션 관리
```bash
# 세션에서 나가기 (백그라운드로 계속 실행)
Ctrl+b, d

# 세션 다시 접속
tmux attach -t faiss_build

# 세션 목록 보기
tmux ls

# 세션 종료 (인덱스 구축 완료 후)
tmux kill-session -t faiss_build
```

## 📊 진행 상황 확인

인덱스 구축 중에는 다음과 같은 로그가 출력됩니다:
```
📦 SentenceTransformer 모델 로딩 중...
✅ 모델 로딩 완료 (device: cpu, dimension: 768)
🔌 DB 연결 중...
✅ 총 537개 레시피 로딩 완료
🧠 임베딩 시작...
```

## ⏱️ 예상 소요 시간

- 모델 로딩: 약 10-30초
- 537개 레시피 임베딩: 약 1-3분 (CPU 기준)
- 총 예상 시간: **2-5분**

## ✅ 완료 확인

인덱스 구축이 완료되면:
```bash
# 인덱스 파일 확인
ls -lh faiss_store/index_new.faiss

# 메타데이터 파일 확인
ls -lh faiss_store/metadata_new.pkl
```

두 파일이 생성되어 있어야 합니다.

## 🔧 문제 해결

### 메모리 부족 오류
- Docker 컨테이너 메모리 증가
- 배치 크기 줄이기 (CHUNK_SIZE 조정)

### 모델 다운로드 오류
- 인터넷 연결 확인
- Hugging Face 토큰 필요할 수 있음

## 📝 다음 단계

인덱스 구축 완료 후:
```bash
# API 테스트
curl -X POST http://localhost:81/api/fastapi/recommend/new \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["김치", "계란", "밥"]}'
```

