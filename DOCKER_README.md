# CookDuck Docker 구성 가이드

## 프로젝트 구조

```
cookduck_backup/
├── backend-server/
│   ├── fastapi/          # FastAPI 메인 서버 (레시피 추천 API)
│   ├── fastapi-gateapi/  # FastAPI GateAPI 서버 (WebSocket 음성 채팅)
│   ├── spring/           # Spring Boot 서버
│   └── nginx/            # Nginx 리버스 프록시
├── frontend/             # Flutter 웹 앱 (정적 파일)
└── docker-compose.yml    # Docker Compose 설정
```

## 서비스 구성

### 1. Nginx (포트 81)
- 리버스 프록시 역할
- FastAPI, Spring Boot로 요청 라우팅
- Flutter 웹 앱 정적 파일 서빙

### 2. FastAPI (포트 8002)
- 레시피 추천 API
- FAISS 벡터 검색
- LangChain 기반 RAG

### 3. FastAPI GateAPI (포트 8003)
- WebSocket 기반 음성 채팅 서버
- STT/TTS 통합

### 4. Spring Boot (포트 8080)
- REST API 서버
- 사용자 인증/인가
- 데이터 관리

### 5. MariaDB (포트 3307)
- 데이터베이스 서버
- 레시피 데이터 저장

## 시작하기

### 1. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값 수정:

```bash
cp .env.example .env
```

### 2. Docker Compose 실행

```bash
# 모든 서비스 빌드 및 시작
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f fastapi
```

### 3. 서비스 중지

```bash
# 서비스 중지 (볼륨 유지)
docker-compose down

# 서비스 중지 및 볼륨 삭제
docker-compose down -v
```

## 개별 서비스 관리

### 특정 서비스만 시작/중지

```bash
# 특정 서비스 시작
docker-compose up -d fastapi

# 특정 서비스 중지
docker-compose stop fastapi

# 특정 서비스 재시작
docker-compose restart fastapi
```

### 컨테이너 접속

```bash
# FastAPI 컨테이너 접속
docker-compose exec fastapi bash

# MariaDB 접속
docker-compose exec mariadb mysql -uroot -proot recipe_db
```

## 볼륨 관리

### MariaDB 데이터 백업

```bash
# 백업
docker-compose exec mariadb mysqldump -uroot -proot recipe_db > backup.sql

# 복원
docker-compose exec -T mariadb mysql -uroot -proot recipe_db < backup.sql
```

## 네트워크

모든 서비스는 `cookduck-network` 브리지 네트워크에 연결되어 있습니다.

서비스 간 통신은 서비스 이름으로 접근 가능:
- `http://fastapi:8000`
- `http://spring:8080`
- `http://mariadb:3306`

## 포트 매핑

| 서비스 | 컨테이너 포트 | 호스트 포트 | 환경 변수 |
|--------|--------------|------------|-----------|
| Nginx | 80 | 81 | `NGINX_PORT` |
| FastAPI | 8000 | 8002 | `FASTAPI_PORT` |
| FastAPI GateAPI | 8000 | 8003 | `FASTAPI_GATEAPI_PORT` |
| Spring Boot | 8080 | 8080 | `SPRING_PORT` |
| MariaDB | 3306 | 3307 | `MARIADB_PORT` |

## 헬스체크

모든 서비스는 헬스체크를 지원합니다:

```bash
# 서비스 상태 확인
docker-compose ps

# 헬스체크 상태 확인
docker inspect cookduck-fastapi | grep -A 10 Health
```

## 문제 해결

### 포트 충돌

포트가 이미 사용 중인 경우 `.env` 파일에서 포트를 변경:

```bash
NGINX_PORT=8081
FASTAPI_PORT=8003
```

### 빌드 실패

캐시 없이 재빌드:

```bash
docker-compose build --no-cache
```

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그 (마지막 100줄)
docker-compose logs --tail=100 fastapi

# 실시간 로그
docker-compose logs -f
```

### 데이터베이스 연결 문제

MariaDB가 완전히 시작될 때까지 대기하도록 `depends_on`에 `condition: service_healthy`가 설정되어 있습니다.

수동으로 확인:

```bash
docker-compose exec mariadb mysqladmin ping -h localhost -uroot -proot
```

## 개발 모드

### 코드 변경 시 자동 반영

FastAPI는 볼륨 마운트를 사용하므로 코드 변경 시 자동으로 반영됩니다.

Spring Boot는 재빌드가 필요할 수 있습니다:

```bash
docker-compose up -d --build spring
```

## 프로덕션 배포

1. `.env` 파일에서 프로덕션 설정 확인
2. `SPRING_PROFILES_ACTIVE=prod` 설정
3. 데이터베이스 비밀번호 변경
4. HTTPS 설정 (Nginx)

## 추가 정보

- FastAPI Swagger: http://localhost:81/docs
- Spring Boot API: http://localhost:8080
- MariaDB: localhost:3307

