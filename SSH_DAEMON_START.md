# SSH 데몬 시작 가이드

## 문제 진단

현재 상태:
- ✅ `Remote Login: On` - SSH 서버 설정은 활성화됨
- ❌ `ps aux | grep sshd` - SSH 데몬이 실행 중이 아님
- ❌ `netstat -an | grep :22` - 포트 22가 열려있지 않음

**결론**: SSH 서버가 설정상 활성화되어 있지만 실제 데몬이 시작되지 않았습니다.

## 해결 방법

### 방법 1: 시스템 설정으로 재시작 (가장 간단)

1. **시스템 설정** → **일반** → **공유**
2. **원격 로그인** 토글을 **끄기**로 변경
3. 잠시 대기 (2-3초)
4. **원격 로그인** 토글을 다시 **켜기**로 변경

### 방법 2: 터미널 명령어로 재시작

터미널에서 다음 명령어를 순서대로 실행:

```bash
# 1. SSH 서버 끄기
sudo systemsetup -setremotelogin off

# 2. 잠시 대기
sleep 2

# 3. SSH 서버 켜기
sudo systemsetup -setremotelogin on

# 4. SSH 데몬 상태 확인
ps aux | grep sshd | grep -v grep

# 5. 포트 22 확인
netstat -an | grep :22
```

### 방법 3: launchctl로 직접 시작

```bash
# SSH 서비스 시작
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist

# 또는
sudo launchctl start com.openssh.sshd

# 상태 확인
sudo launchctl list | grep ssh
```

## 확인 방법

SSH 데몬이 정상적으로 시작되었는지 확인:

```bash
# 1. SSH 데몬 프로세스 확인
ps aux | grep sshd | grep -v grep
# 결과: sshd 프로세스가 보여야 함

# 2. 포트 22 확인
netstat -an | grep :22
# 결과: LISTEN 상태로 포트 22가 열려있어야 함

# 3. 로컬에서 테스트
ssh parkkeonryul@localhost
# 성공하면 비밀번호 입력 프롬프트가 나타남
```

## 예상 결과

정상적으로 시작되면:

```bash
$ ps aux | grep sshd | grep -v grep
root   1234  0.0  0.1  ...  /usr/sbin/sshd

$ netstat -an | grep :22
tcp46      0      0  *.22                  *.*                    LISTEN
```

## 문제가 계속되면

1. **방화벽 확인**
   - 시스템 설정 → 네트워크 → 방화벽
   - 방화벽 옵션 → 원격 로그인(SSH) 체크

2. **로그 확인**
   ```bash
   sudo log show --predicate 'process == "sshd"' --last 10m --style syslog
   ```

3. **시스템 재부팅**
   - 간혹 재부팅으로 해결되는 경우가 있습니다

