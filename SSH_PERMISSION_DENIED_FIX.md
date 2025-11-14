# SSH "Permission denied" 에러 해결 방법

## 발생 원인

SSH 접속 시 "Permission denied, please try again." 에러가 발생하는 주요 원인:

1. **비밀번호가 틀렸을 때**
2. **SSH 서버가 비밀번호 인증을 허용하지 않을 때**
3. **사용자가 원격 로그인에 허용되지 않았을 때**
4. **SSH 서버가 실행되지 않았을 때**

## 해결 방법

### 1. SSH 서버 활성화 확인

MacBook에서 다음 명령어 실행:

```bash
# SSH 서버 상태 확인
sudo systemsetup -getremotelogin

# "Remote Login: On" 이 나와야 합니다
# "Off"인 경우 아래 명령어로 활성화:
sudo systemsetup -setremotelogin on
```

또는 **시스템 설정** → **일반** → **공유** → **원격 로그인** 토글이 **켜기**인지 확인

### 2. 사용자 계정 확인

원격 로그인 설정에서 현재 사용자(`parkkeonryul`)가 허용되어 있는지 확인:

1. **시스템 설정** → **일반** → **공유** → **원격 로그인**
2. **접근 허용** 목록에 `parkkeonryul`이 있는지 확인
3. 없으면 추가

### 3. SSH 설정 확인 및 수정

터미널에서 SSH 설정 파일 확인:

```bash
# SSH 설정 파일 확인
sudo nano /etc/ssh/sshd_config
```

다음 설정이 올바른지 확인:

```bash
# 비밀번호 인증 허용
PasswordAuthentication yes

# 공개키 인증 허용
PubkeyAuthentication yes

# Root 로그인 (일반 사용자는 no로 설정)
PermitRootLogin no
```

설정 변경 후 SSH 서버 재시작:

```bash
# SSH 서버 재시작
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd

# 또는
sudo systemsetup -setremotelogin off
sudo systemsetup -setremotelogin on
```

### 4. 비밀번호 확인

MacBook 사용자 계정 비밀번호를 정확히 입력했는지 확인:

```bash
# MacBook에서 비밀번호 테스트
# 로컬에서 로그인할 수 있는 비밀번호가 SSH 접속 비밀번호입니다
```

### 5. 방화벽 확인

방화벽이 SSH를 차단하고 있는지 확인:

1. **시스템 설정** → **네트워크** → **방화벽**
2. **방화벽 옵션** 클릭
3. **원격 로그인(SSH)** 체크박스가 활성화되어 있는지 확인

### 6. SSH 로그 확인

접속 시도 시 로그 확인:

```bash
# MacBook에서 실행 (실시간 모니터링)
sudo log stream --predicate 'process == "sshd" OR eventMessage contains "ssh" OR eventMessage contains "Failed password"' --style syslog

# 또는 최근 로그 확인
sudo log show --predicate 'process == "sshd" OR eventMessage contains "ssh" OR eventMessage contains "Failed password" OR eventMessage contains "Connection"' --last 30m --style syslog | grep -i -E "(ssh|password|connection|denied|failed)"

# 또는 간단하게
sudo log show --predicate 'eventMessage contains "ssh"' --last 10m --style syslog
```

**로그 확인 결과 해석:**
- SSH 서버가 활성화되어 있으면: `Setting service com.openssh.sshd to enabled` 메시지가 보입니다
- 실제 접속 시도가 있으면: `Connection from`, `Failed password`, `Accepted password` 등의 메시지가 보입니다
- 아무 로그도 안 보이면: SSH 서버가 접속을 받지 못하고 있거나, 방화벽이 차단하고 있을 수 있습니다

### 7. SSH 키 인증 사용 (권장)

비밀번호 대신 SSH 키를 사용하면 더 안전하고 편리합니다:

#### MacBook에서 공개키 생성 (이미 있는 경우 스킵)

```bash
# SSH 키가 있는지 확인
ls -la ~/.ssh/

# 없으면 생성
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

#### 다른 PC에서 공개키를 MacBook에 복사

```bash
# 다른 PC에서 실행
ssh-copy-id parkkeonryul@192.168.0.35

# 또는 수동으로
cat ~/.ssh/id_rsa.pub | ssh parkkeonryul@192.168.0.35 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

#### SSH 키로 접속

```bash
ssh -i ~/.ssh/id_rsa parkkeonryul@192.168.0.35
```

### 8. 빠른 해결 체크리스트

- [ ] 시스템 설정에서 원격 로그인 활성화 확인
- [ ] **SSH 데몬이 실제로 실행 중인지 확인** (`ps aux | grep sshd`)
- [ ] **포트 22가 열려있는지 확인** (`netstat -an | grep :22`)
- [ ] 사용자 계정이 원격 로그인 허용 목록에 있는지 확인
- [ ] MacBook 사용자 계정 비밀번호 정확히 입력
- [ ] 방화벽에서 SSH 허용 확인
- [ ] SSH 서버 재시작 (끄고 다시 켜기)
- [ ] SSH 설정 파일에서 `PasswordAuthentication yes` 확인

### 9. 중요: SSH 데몬이 실행 중이 아닌 경우

`ps aux | grep sshd` 결과가 비어있으면 SSH 데몬이 실행되지 않은 것입니다.

**해결 방법:**
1. 시스템 설정 → 일반 → 공유 → 원격 로그인: 끄기 → 켜기
2. 또는 터미널에서: `sudo systemsetup -setremotelogin off && sleep 2 && sudo systemsetup -setremotelogin on`

자세한 내용은 `SSH_DAEMON_START.md` 파일을 참고하세요.

## 테스트 방법

### 로컬에서 테스트

MacBook에서 자신에게 SSH 접속 시도:

```bash
ssh parkkeonryul@localhost
```

성공하면 SSH 서버는 정상 작동 중입니다.

### 다른 PC에서 테스트

```bash
# 로컬 네트워크에서
ssh parkkeonryul@192.168.0.35

# 외부에서 (포트 포워딩 설정 후)
ssh parkkeonryul@221.160.134.10 -p 2202
```

## 추가 문제 해결

### 포트 확인

```bash
# SSH 포트가 열려있는지 확인
sudo lsof -i :22

# 다른 포트 사용 중인지 확인
sudo lsof -i | grep ssh
```

### 사용자 그룹 확인

```bash
# SSH 접근 그룹 확인
dscl . -read /Groups/com.apple.access_ssh

# 사용자가 그룹에 속해있는지 확인
id parkkeonryul | grep ssh
```

## 참고

- SSH 서버는 macOS에 기본적으로 포함되어 있습니다
- 시스템 설정에서 원격 로그인을 켜면 자동으로 활성화됩니다
- 보안을 위해 SSH 키 인증 사용을 강력히 권장합니다

