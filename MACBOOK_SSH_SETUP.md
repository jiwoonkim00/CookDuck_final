# MacBook SSH 서버 설정 가이드

## MacBook 정보
- **로컬 IP 주소**: `192.168.0.35` (현재 확인된 주소)
- **공인 IP 주소**: `221.160.134.10` (현재 확인된 주소)
- **사용자명**: `parkkeonryul` (현재 사용자)
- **프로젝트 경로**: `/Users/parkkeonryul/Desktop/cookduck_backup 2/`

## 1. MacBook에서 SSH 서버 활성화

### 방법 1: 시스템 설정 GUI 사용 (권장)

1. **시스템 설정** 열기
2. **일반** → **공유** 클릭
3. **원격 로그인** 항목 찾기
4. **원격 로그인** 토글 스위치를 **켜기**로 변경
5. 접속할 사용자 선택 (현재 사용자 `parkkeonryul` 허용)

### 방법 2: 터미널 명령어 사용

```bash
# SSH 서버 활성화 (관리자 권한 필요)
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

MacBook의 방화벽이 활성화되어 있다면 SSH 포트(22)를 허용해야 합니다:

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

```powershell
ssh parkkeonryul@192.168.0.35
```

### Mac/Linux PC에서 접속

```bash
ssh parkkeonryul@192.168.0.35
```

### 첫 접속 시

첫 접속 시 SSH 키 확인 메시지가 나타납니다:
```
The authenticity of host '192.168.0.35' can't be established.
Are you sure you want to continue connecting (yes/no)?
```
`yes`를 입력하고 Enter를 누르세요.

## 4. 프로젝트 파일 접근

SSH 접속 후:

```bash
# 프로젝트 디렉토리로 이동
cd ~/Desktop/cookduck_backup\ 2/

# 프론트엔드 파일 확인
cd frontend/lib/
ls -la

# 백엔드 파일 확인
cd ../backend-server/fastapi/app/
ls -la
```

## 5. 외부에서 접속하기 (인터넷을 통한 원격 접속)

### 5.1 공인 IP 주소 확인

MacBook에서 다음 명령어로 공인 IP 확인:

```bash
curl ifconfig.me
# 또는
curl icanhazip.com
```

### 5.2 라우터 포트 포워딩 설정

인터넷을 통해 접속하려면 라우터에서 포트 포워딩 설정이 필요합니다:

1. **라우터 관리 페이지 접속**
   - 일반적으로 `192.168.0.1` 또는 `192.168.1.1`
   - 브라우저에서 접속

2. **포트 포워딩 설정 추가**
   - 메뉴: **포트 포워딩** 또는 **Virtual Server** 또는 **NAT 설정**
   - 설정 항목:
     - **외부 포트**: `2202` (또는 원하는 포트, 22는 보안상 권장하지 않음)
     - **내부 IP**: `192.168.0.35` (MacBook의 로컬 IP)
     - **내부 포트**: `22` (SSH 기본 포트)
     - **프로토콜**: `TCP`
     - **설명**: `MacBook SSH` (선택사항)

3. **설정 저장 및 적용**

### 5.3 외부에서 접속

포트 포워딩 설정 후:

```bash
# 기본 명령어
ssh parkkeonryul@공인_IP주소 -p 2202

# 예시 (공인 IP가 123.45.67.89인 경우)
ssh parkkeonryul@123.45.67.89 -p 2202
```

### 5.4 동적 IP 주소 처리 (DDNS)

공인 IP가 자주 바뀌는 경우 DDNS 서비스를 사용:

1. **DDNS 서비스 가입** (예: No-IP, DuckDNS, Dynu)
2. **호스트명 설정** (예: `my-macbook.ddns.net`)
3. **라우터에 DDNS 설정** 또는 **MacBook에 DDNS 클라이언트 설치**

접속:
```bash
ssh parkkeonryul@my-macbook.ddns.net -p 2202
```

### 5.5 보안 강화 (권장)

외부 접속 시 보안을 강화하세요:

1. **SSH 키 인증 사용** (비밀번호 대신)
2. **포트 변경** (22 대신 다른 포트 사용)
3. **fail2ban 설치** (무차별 대입 공격 방지)
4. **특정 IP만 허용** (가능한 경우)

## 6. 현재 설정 확인

```bash
# MacBook IP 주소 확인
ifconfig | grep "inet " | grep -v 127.0.0.1

# SSH 서버 상태 확인
sudo systemsetup -getremotelogin

# SSH 포트 확인
sudo lsof -i :22
```

## 7. 빠른 참조

```bash
# 다른 PC에서 MacBook 접속
ssh parkkeonryul@192.168.0.35

# 프로젝트 디렉토리로 바로 이동
ssh parkkeonryul@192.168.0.35 "cd ~/Desktop/cookduck_backup\ 2/ && pwd"

# 특정 포트로 접속 (포트 포워딩 설정된 경우)
ssh -p 2202 parkkeonryul@공인_IP주소
```

## 8. "Permission denied" 에러 해결

SSH 접속 시 "Permission denied, please try again." 에러가 발생하는 경우:

### 빠른 해결 방법

1. **시스템 설정 확인**
   - 시스템 설정 → 일반 → 공유 → 원격 로그인
   - 토글이 **켜기**인지 확인
   - 접근 허용 목록에 `parkkeonryul`이 있는지 확인

2. **SSH 서버 재시작**
   ```bash
   sudo systemsetup -setremotelogin off
   sudo systemsetup -setremotelogin on
   ```

3. **비밀번호 확인**
   - MacBook 사용자 계정 비밀번호를 정확히 입력
   - 로컬 로그인 비밀번호와 동일합니다

4. **방화벽 확인**
   - 시스템 설정 → 네트워크 → 방화벽
   - 방화벽 옵션 → 원격 로그인(SSH) 체크

자세한 해결 방법은 `SSH_PERMISSION_DENIED_FIX.md` 파일을 참고하세요.

## 9. Docker 컨테이너와의 차이

- **MacBook SSH 접속**: 로컬 파일 시스템에 직접 접근 (`/Users/parkkeonryul/Desktop/cookduck_backup 2/`)
- **Docker 컨테이너 SSH 접속**: 컨테이너 내부 파일 시스템 접근 (포트 2202, 2203, 2204)

프로젝트 파일을 수정하려면 **MacBook에 직접 SSH 접속**해야 합니다.

## 현재 MacBook 정보

- **로컬 IP 주소**: `192.168.0.35`
- **공인 IP 주소**: `221.160.134.10` (현재 확인된 주소)
- **사용자명**: `parkkeonryul`
- **SSH 포트**: `22` (기본)
- **로컬 접속 명령어**: `ssh parkkeonryul@192.168.0.35`
- **외부 접속 명령어**: `ssh parkkeonryul@221.160.134.10 -p 2202` (포트 포워딩 설정 후)
- **프로젝트 경로**: `/Users/parkkeonryul/Desktop/cookduck_backup 2/`

## 외부 접속 빠른 가이드

### 1단계: 라우터 포트 포워딩 설정

라우터 관리 페이지(`192.168.0.1` 또는 `192.168.1.1`)에서:

- **외부 포트**: `2202`
- **내부 IP**: `192.168.0.35`
- **내부 포트**: `22`
- **프로토콜**: `TCP`

### 2단계: 외부에서 접속

```bash
ssh parkkeonryul@221.160.134.10 -p 2202
```

### 3단계: 프로젝트 파일 수정

```bash
# 접속 후
cd ~/Desktop/cookduck_backup\ 2/

# 프론트엔드 파일 수정
cd frontend/lib/screens/
vim chat_screen.dart  # 또는 원하는 에디터

# 백엔드 파일 수정
cd ../../backend-server/fastapi/app/
vim main.py
```

