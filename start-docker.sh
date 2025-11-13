#!/bin/bash

# Docker Compose 자동 시작 스크립트
cd "$(dirname "$0")"

# Docker Desktop이 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
    echo "Docker Desktop이 실행되지 않았습니다. 시작합니다..."
    open -a Docker
    # Docker가 완전히 시작될 때까지 대기
    echo "Docker Desktop 시작 대기 중..."
    while ! docker info > /dev/null 2>&1; do
        sleep 2
    done
    echo "Docker Desktop이 시작되었습니다."
fi

# Docker Compose 시작
echo "Docker Compose 서비스 시작 중..."
docker compose up -d

echo "서비스가 시작되었습니다."
docker compose ps

