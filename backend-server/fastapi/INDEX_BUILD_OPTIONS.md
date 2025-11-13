# FAISS 인덱스 구축 방법 (tmux 없이)

## 방법 1: nohup 사용 (권장) ✅

백그라운드에서 실행하고 로그 파일로 확인:

```bash
cd /Users/keonryul/Desktop/cookduck_backup/backend-server/fastapi

# 백그라운드로 실행
nohup python3 build_faiss_new_table.py > faiss_build.log 2>&1 &

# 진행 상황 실시간 확인
tail -f faiss_build.log

# 프로세스 확인
ps aux | grep build_faiss_new_table

# 프로세스 종료 (필요시)
pkill -f build_faiss_new_table.py
```

## 방법 2: 쉘 스크립트 사용 ✅

제공된 스크립트 사용:

```bash
cd /Users/keonryul/Desktop/cookduck_backup/backend-server/fastapi

# 스크립트 실행
./build_index_background.sh

# 로그 확인
tail -f faiss_build.log
```

## 방법 3: 일반 실행 후 Ctrl+Z 사용

```bash
cd /Users/keonryul/Desktop/cookduck_backup/backend-server/fastapi

# 실행 시작
python3 build_faiss_new_table.py

# Ctrl+Z로 일시정지 후 백그라운드로 보내기
bg

# 작업 확인
jobs

# 다시 포그라운드로 (필요시)
fg
```

## 방법 4: tmux 설치 후 사용 (선택사항)

Homebrew로 tmux 설치:

```bash
# Homebrew가 있다면
brew install tmux

# 그 다음 사용
tmux new -s faiss_build
python3 build_faiss_new_table.py
# Ctrl+b, d 로 나가기
```

## 📊 진행 상황 확인

실시간 로그 보기:
```bash
tail -f faiss_build.log
```

프로세스 상태 확인:
```bash
ps aux | grep build_faiss_new_table
```

## ✅ 완료 확인

인덱스 파일 생성 확인:
```bash
ls -lh faiss_store/index_new.faiss faiss_store/metadata_new.pkl
```

로그에서 "✅ 전체 임베딩 및 저장 완료!" 메시지 확인:
```bash
grep "완료" faiss_build.log
```

