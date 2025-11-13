# SSH 접속 가이드

## 개요

모든 백엔드 서비스 컨테이너에 SSH 서버가 설치되어 있습니다. 이를 통해 컨테이너에 직접 SSH 접속이 가능합니다.

## SSH 포트 매핑

| 서비스 | SSH 포트 | 환경 변수 | 기본 포트 |
|--------|----------|-----------|----------|
| FastAPI | 2202 | `FASTAPI_SSH_PORT` | 2202 |
| FastAPI GateAPI | 2203 | `FASTAPI_GATEAPI_SSH_PORT` | 2203 |
| Spring Boot | 2204 | `SPRING_SSH_PORT` | 2204 |

## 접속 정보

### 기본 접속 정보
- **사용자명**: `root`
- **비밀번호**: 환경 변수 `SSH_ROOT_PASSWORD`로 설정 (기본값: `root123`)
- **호스트**: `localhost`
- **포트**: 각 서비스별 SSH 포트 (위 표 참조)

## SSH 접속 방법

### 1. FastAPI 컨테이너 접속

```bash
ssh root@localhost -p 2202
# 비밀번호: root123 (또는 .env에서 설정한 값)
```

### 2. FastAPI GateAPI 컨테이너 접속

```bash
ssh root@localhost -p 2203
# 비밀번호: root123 (또는 .env에서 설정한 값)
```

### 3. Spring Boot 컨테이너 접속

```bash
ssh root@localhost -p 2204
# 비밀번호: root123 (또는 .env에서 설정한 값)
```

## 비밀번호 변경

`.env` 파일에서 `SSH_ROOT_PASSWORD` 환경 변수를 수정하고 컨테이너를 재시작하세요:

```bash
# .env 파일 수정
SSH_ROOT_PASSWORD=새로운비밀번호

# 컨테이너 재시작
docker compose restart fastapi fastapi-gateapi spring
```

## SSH 키 인증 설정 (선택사항)

SSH 키를 사용하여 비밀번호 없이 접속할 수 있습니다.

### 1. SSH 키 생성 (이미 있다면 생략)

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/cookduck_key
```

### 2. 공개키를 컨테이너에 복사

```bash
# FastAPI 컨테이너에 공개키 복사
ssh-copy-id -i ~/.ssh/cookduck_key.pub -p 2202 root@localhost

# 또는 수동으로 복사
cat ~/.ssh/cookduck_key.pub | ssh root@localhost -p 2202 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. SSH 키로 접속

```bash
ssh -i ~/.ssh/cookduck_key -p 2202 root@localhost
```

## 보안 권장사항

### 프로덕션 환경

프로덕션 환경에서는 다음 보안 설정을 권장합니다:

1. **강력한 비밀번호 사용**
   ```bash
   SSH_ROOT_PASSWORD=복잡한비밀번호123!@#
   ```

2. **SSH 키 인증만 허용** (비밀번호 인증 비활성화)
   - `sshd_config` 파일에서 `PasswordAuthentication no` 설정

3. **포트 변경**
   - 잘 알려진 포트를 피하고 다른 포트 사용

4. **방화벽 설정**
   - 필요한 IP만 접속 허용

## 문제 해결

### SSH 연결 실패

1. **컨테이너가 실행 중인지 확인**
   ```bash
   docker compose ps
   ```

2. **SSH 서비스가 실행 중인지 확인**
   ```bash
   docker compose exec fastapi ps aux | grep sshd
   ```

3. **포트가 올바르게 매핑되었는지 확인**
   ```bash
   docker compose ps | grep 22
   ```

4. **로그 확인**
   ```bash
   docker compose logs fastapi | grep ssh
   ```

### 비밀번호로 접속이 안 될 때

1. **비밀번호 확인**
   ```bash
   # .env 파일 확인
   cat .env | grep SSH_ROOT_PASSWORD
   ```

2. **컨테이너 재시작**
   ```bash
   docker compose restart fastapi
   ```

3. **SSH 서버 재시작**
   ```bash
   docker compose exec fastapi /usr/sbin/sshd
   ```

## 대안: Docker exec 사용

SSH 대신 Docker exec를 사용할 수도 있습니다:

```bash
# FastAPI 컨테이너 접속
docker compose exec fastapi bash

# Spring Boot 컨테이너 접속
docker compose exec spring sh

# MariaDB 접속
docker compose exec mariadb mysql -uroot -proot recipe_db
```

Docker exec는 SSH보다 더 가볍고 빠르지만, 네트워크를 통한 원격 접속이 필요할 때는 SSH가 유용합니다.

