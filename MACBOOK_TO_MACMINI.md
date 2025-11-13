# 맥북에서 맥미니로 SSH 접속 가이드

## 빠른 접속 방법

### 1. 터미널 열기

맥북에서 **터미널(Terminal)** 앱을 실행하세요:
- `Cmd + Space` → "터미널" 또는 "Terminal" 입력
- 또는 **응용 프로그램** → **유틸리티** → **터미널**

### 2. 기본 접속 명령어

```bash
ssh server@192.168.0.45
```

### 3. 첫 접속 시

첫 접속 시 다음과 같은 메시지가 나타납니다:
```
The authenticity of host '192.168.0.45 (192.168.0.45)' can't be established.
ED25519 key fingerprint is SHA256:xxxxx...
Are you sure you want to continue connecting (yes/no/[fingerprint])? 
```

`yes`를 입력하고 Enter를 누르세요.

### 4. 비밀번호 입력

맥미니의 `server` 사용자 비밀번호를 입력하세요:
```
server@192.168.0.45's password:
```

비밀번호는 화면에 표시되지 않지만 정상적으로 입력되고 있습니다.

## 접속 방법 옵션

### 방법 1: IP 주소로 접속 (가장 일반적)

```bash
ssh server@192.168.0.45
```

### 방법 2: 호스트명으로 접속

```bash
ssh server@serverui-Macmini.local
```

### 방법 3: 사용자명 생략 (현재 맥북 사용자명과 동일한 경우)

```bash
ssh 192.168.0.45
```

## SSH 키로 비밀번호 없이 접속하기

### 1. SSH 키 생성 (맥북에서 - 처음 한 번만)

```bash
# SSH 키가 없으면 생성
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Enter를 여러 번 눌러 기본 설정 사용
# 비밀번호는 선택사항 (설정하면 더 안전)
```

### 2. 공개키를 맥미니에 복사

```bash
# 자동으로 복사 (가장 간편)
ssh-copy-id server@192.168.0.45
```

이 명령어를 실행하면:
1. 맥미니 비밀번호를 한 번 입력
2. 공개키가 자동으로 맥미니에 복사됨
3. 이후부터는 비밀번호 없이 접속 가능

### 3. 비밀번호 없이 접속

```bash
ssh server@192.168.0.45
```

이제 비밀번호 입력 없이 바로 접속됩니다!

## 고급 설정

### SSH 설정 파일 생성 (선택사항)

맥북에서 `~/.ssh/config` 파일을 생성하면 접속을 더 편리하게 할 수 있습니다:

```bash
# 설정 파일 편집
nano ~/.ssh/config
```

다음 내용 추가:

```
Host macmini
    HostName 192.168.0.45
    User server
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

이제 다음 명령어로 간단하게 접속:

```bash
ssh macmini
```

### 접속 후 Docker 컨테이너 접속

맥미니에 접속한 후, Docker 컨테이너에 접속:

```bash
# 맥미니에 접속
ssh server@192.168.0.45

# Docker 컨테이너 목록 확인
cd ~/Desktop/cookduck_backup
docker compose ps

# FastAPI 컨테이너 접속
ssh root@localhost -p 2202
# 또는
docker compose exec fastapi bash

# Spring Boot 컨테이너 접속
ssh root@localhost -p 2204
# 또는
docker compose exec spring sh
```

## 문제 해결

### 1. "Connection refused" 오류

맥미니에서 SSH 서버가 활성화되어 있는지 확인:
```bash
# 맥미니에서 실행
sudo systemsetup -getremotelogin
# "Remote Login: On" 이어야 함
```

### 2. "Host key verification failed" 오류

```bash
# 맥북에서 실행
ssh-keygen -R 192.168.0.45
```

### 3. 네트워크 연결 확인

```bash
# 맥북에서 실행
ping 192.168.0.45

# SSH 포트 확인
nc -zv 192.168.0.45 22
```

### 4. 상세 로그로 접속 시도

```bash
ssh -v server@192.168.0.45
```

## 유용한 명령어

### 접속 후 바로 명령 실행

```bash
# 맥미니에 접속하지 않고 바로 명령 실행
ssh server@192.168.0.45 "docker compose ps"

# 여러 명령 실행
ssh server@192.168.0.45 "cd ~/Desktop/cookduck_backup && docker compose logs -f"
```

### 파일 전송 (SCP)

```bash
# 맥북 → 맥미니로 파일 전송
scp 파일명 server@192.168.0.45:~/Desktop/

# 맥미니 → 맥북으로 파일 다운로드
scp server@192.168.0.45:~/Desktop/파일명 ~/Downloads/

# 폴더 전체 전송
scp -r 폴더명 server@192.168.0.45:~/Desktop/
```

### 파일 동기화 (rsync)

```bash
# 맥북 → 맥미니로 동기화
rsync -avz ~/Desktop/project/ server@192.168.0.45:~/Desktop/project/

# 맥미니 → 맥북으로 동기화
rsync -avz server@192.168.0.45:~/Desktop/project/ ~/Desktop/project/
```

## 포트 포워딩 (터널링)

### 로컬 포트 포워딩

```bash
# 맥미니의 8002 포트를 맥북의 8002로 포워딩
ssh -L 8002:localhost:8002 server@192.168.0.45

# 접속 후 브라우저에서 http://localhost:8002 접속
```

### 원격 포트 포워딩

```bash
# 맥북의 8080 포트를 맥미니의 8080으로 포워딩
ssh -R 8080:localhost:8080 server@192.168.0.45
```

## 빠른 참조

```bash
# 기본 접속
ssh server@192.168.0.45

# 호스트명으로 접속
ssh server@serverui-Macmini.local

# SSH 키 설정
ssh-copy-id server@192.168.0.45

# 파일 전송
scp 파일 server@192.168.0.45:~/Desktop/

# 원격 명령 실행
ssh server@192.168.0.45 "docker compose ps"
```

## 현재 설정 정보

- **맥미니 IP**: `192.168.0.45`
- **맥미니 호스트명**: `serverui-Macmini.local`
- **사용자명**: `server`
- **SSH 포트**: `22`
- **접속 명령어**: `ssh server@192.168.0.45`

