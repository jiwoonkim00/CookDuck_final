#!/bin/bash
# FAISS 인덱스 구축 스크립트 (백그라운드 실행)

cd /Users/keonryul/Desktop/cookduck_backup/backend-server/fastapi

echo "🚀 FAISS 인덱스 구축 시작..."
echo "📝 로그 파일: faiss_build.log"
echo ""

# 백그라운드로 실행하고 로그 저장
nohup python3 build_faiss_new_table.py > faiss_build.log 2>&1 &

PID=$!
echo "✅ 프로세스 시작됨 (PID: $PID)"
echo ""
echo "진행 상황 확인:"
echo "  tail -f faiss_build.log"
echo ""
echo "프로세스 상태 확인:"
echo "  ps aux | grep build_faiss_new_table"
echo ""
echo "프로세스 종료:"
echo "  kill $PID"

