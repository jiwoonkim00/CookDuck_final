# 맥미니 SSH 서버 설정 가이드

## 맥미니 정보
- **IP 주소**: `192.168.0.45` (현재 확인된 주소)
- **사용자명**: `server` (현재 사용자)

## 1. 맥미니에서 SSH 서버 활성화

### 방법 1: 시스템 설정 GUI 사용 (권장)

1. **시스템 설정** 열기
2. **일반** → **공유** 클릭
3. **원격 로그인** 항목 찾기
4. **원격 로그인** 토글 스위치를 **켜기**로 변경
5. 필요시 접속할 사용자 선택 (현재 사용자 `server` 허용)

### 방법 2: 터미널 명령어 사용

```bash
# SSH 서버 활성화
sudo systemsetup -setremotelogin on

# SSH 서버 상태 확인
sudo systemsetup -getremotelogin
```

또는:

```bash
# SSH 서버 활성화
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist

# SSH 서버 상태 확인
sudo launchctl list | grep ssh
```

## 2. 방화벽 설정

맥미니의 방화벽이 활성화되어 있다면 SSH 포트(22)를 허용해야 합니다:

1. **시스템 설정** → **네트워크** → **방화벽**
2. **방화벽 옵션** 클릭
3. **원격 로그인(SSH)** 체크박스 활성화

또는 터미널에서:

```bash
# 방화벽에서 SSH 허용
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/sbin/sshd
```

## 3. 다른 PC에서 접속하기

### Windows PC에서 접속

#### 방법 1: PowerShell 사용

```powershell
ssh server@192.168.0.45
```

#### 방법 2: PuTTY 사용

1. PuTTY 다운로드 및 설치
2. 호스트 이름: `192.168.0.45`
3. 포트: `22`
4. 연결 타입: `SSH`
5. 열기 클릭

#### 방법 3: Windows Terminal 사용

```bash
ssh server@192.168.0.45
```

### Mac/Linux PC에서 접속

```bash
ssh server@192.168.0.45
```

### 첫 접속 시

첫 접속 시 SSH 키 확인 메시지가 나타납니다:
```
The authenticity of host '192.168.0.45' can't be established.
Are you sure you want to continue connecting (yes/no)?
```
`yes`를 입력하고 Enter를 누르세요.

## 4. 비밀번호 없이 접속하기 (SSH 키 사용)

### SSH 키 생성 (다른 PC에서)

```bash
# SSH 키 생성
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 생성된 공개키 확인
cat ~/.ssh/id_rsa.pub
```

### 공개키를 맥미니에 복사

#### 방법 1: ssh-copy-id 사용 (가장 간편)

```bash
ssh-copy-id server@192.168.0.45
```

#### 방법 2: 수동 복사

1. 다른 PC에서 공개키 복사:
```bash
cat ~/.ssh/id_rsa.pub | pbcopy  # Mac
# 또는
cat ~/.ssh/id_rsa.pub           # 출력된 내용 복사
```

2. 맥미니에 접속 후:
```bash
ssh server@192.168.0.45
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "복사한_공개키_내용" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### 방법 3: 한 줄 명령어

```bash
cat ~/.ssh/id_rsa.pub | ssh server@192.168.0.45 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

## 5. SSH 설정 파일 커스터마이징 (선택사항)

### 맥미니에서 SSH 설정 수정

```bash
sudo nano /etc/ssh/sshd_config
```

주요 설정 옵션:

```bash
# 포트 변경 (기본 22)
Port 2222

# 비밀번호 인증 허용
PasswordAuthentication yes

# Root 로그인 허용 (보안상 권장하지 않음)
PermitRootLogin no

# 공개키 인증 허용
PubkeyAuthentication yes

# 연결 타임아웃
ClientAliveInterval 60
ClientAliveCountMax 3
```

설정 변경 후 SSH 서버 재시작:

```bash
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

## 6. 포트 포워딩 (인터넷을 통한 원격 접속)

인터넷을 통해 접속하려면 라우터에서 포트 포워딩 설정이 필요합니다:

1. 라우터 관리 페이지 접속
2. 포트 포워딩 설정:
   - 외부 포트: `2222` (또는 원하는 포트)
   - 내부 IP: `192.168.0.45`
   - 내부 포트: `22`
   - 프로토콜: `TCP`

3. 외부에서 접속:
```bash
ssh server@공인_IP주소 -p 2222
```

## 7. 보안 권장사항

### 강력한 비밀번호 사용
- 최소 12자 이상
- 대소문자, 숫자, 특수문자 조합

### SSH 키 인증 사용
- 비밀번호보다 안전함
- SSH 키에는 비밀번호 설정 권장

### 포트 변경
- 기본 포트 22 대신 다른 포트 사용 권장
- 예: 2222, 22222 등

### 방화벽 설정
- 특정 IP만 접속 허용
- fail2ban 설치 고려

## 8. 문제 해결

### SSH 연결 실패 시

1. **SSH 서버 상태 확인**
```bash
# 맥미니에서
sudo launchctl list | grep ssh
sudo systemsetup -getremotelogin
```

2. **포트 확인**
```bash
# 맥미니에서
sudo lsof -i :22
```

3. **방화벽 확인**
```bash
# 맥미니에서
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
```

4. **네트워크 연결 확인**
```bash
# 다른 PC에서
ping 192.168.0.45
telnet 192.168.0.45 22
```

5. **SSH 로그 확인**
```bash
# 맥미니에서
tail -f /var/log/system.log | grep ssh
```

## 9. Docker 컨테이너 SSH 접속

맥미니에 접속한 후, Docker 컨테이너에 SSH 접속:

```bash
# 맥미니에 SSH 접속
ssh server@192.168.0.45

# Docker 컨테이너 목록 확인
docker compose ps

# FastAPI 컨테이너 SSH 접속 (맥미니 내부에서)
ssh root@localhost -p 2202

# 또는 직접 접속
docker compose exec fastapi bash
```

## 10. 빠른 참조

```bash
# 맥미니 IP 주소 확인
ifconfig | grep "inet " | grep -v 127.0.0.1

# 다른 PC에서 맥미니 접속
ssh server@192.168.0.45

# SSH 키로 접속
ssh -i ~/.ssh/id_rsa server@192.168.0.45

# 특정 포트로 접속
ssh -p 2222 server@192.168.0.45

# SSH 연결 테스트
ssh -v server@192.168.0.45
```

## 현재 맥미니 정보

- **IP 주소**: `192.168.0.45`
- **사용자명**: `server`
- **SSH 포트**: `22` (기본)
- **접속 명령어**: `ssh server@192.168.0.45`

