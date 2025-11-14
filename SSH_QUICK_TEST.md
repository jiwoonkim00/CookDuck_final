# SSH 접속 빠른 테스트 가이드

## 현재 상태 확인

로그를 보면 SSH 서버는 활성화되어 있습니다:
- `Setting service com.openssh.sshd to enabled` - SSH 서버 활성화됨
- SSH 관련 프로세스들이 실행 중

## 실시간 로그 모니터링

다른 PC에서 접속 시도할 때 실시간으로 로그를 확인하려면:

```bash
# MacBook에서 실행 (새 터미널 창에서)
sudo log stream --predicate 'process == "sshd" OR eventMessage contains "ssh" OR eventMessage contains "Failed password" OR eventMessage contains "Connection"' --style syslog
```

이 명령어를 실행한 상태에서 다른 PC에서 SSH 접속을 시도하면 실시간으로 로그가 표시됩니다.

## 접속 테스트

### 1. 로컬에서 테스트 (MacBook에서)

```bash
# 자신에게 SSH 접속 시도
ssh parkkeonryul@localhost

# 성공하면: 비밀번호 입력 후 접속됨
# 실패하면: 에러 메시지 확인
```

### 2. 다른 PC에서 테스트

```bash
# 로컬 네트워크에서
ssh parkkeonryul@192.168.0.35

# 외부에서 (포트 포워딩 설정 후)
ssh parkkeonryul@221.160.134.10 -p 2202
```

## "Permission denied" 발생 시 확인사항

1. **비밀번호 확인**
   - MacBook 사용자 계정 비밀번호를 정확히 입력
   - 대소문자 구분 확인

2. **시스템 설정 확인**
   - 시스템 설정 → 일반 → 공유 → 원격 로그인
   - 토글이 **켜기**인지 확인
   - **접근 허용** 목록에 `parkkeonryul`이 있는지 확인

3. **방화벽 확인**
   - 시스템 설정 → 네트워크 → 방화벽
   - 방화벽 옵션 → 원격 로그인(SSH) 체크

4. **SSH 서버 재시작**
   ```bash
   sudo systemsetup -setremotelogin off
   sudo systemsetup -setremotelogin on
   ```

## 로그에서 확인할 수 있는 정보

접속 시도 시 로그에 나타나는 메시지:

- **성공한 접속**: `Accepted password for parkkeonryul`
- **실패한 접속**: `Failed password for parkkeonryul`
- **연결 시도**: `Connection from [IP주소]`
- **권한 거부**: `Permission denied`

## 문제 해결 순서

1. 로컬에서 `ssh parkkeonryul@localhost` 테스트
2. 실패하면 시스템 설정에서 원격 로그인 확인
3. 성공하면 다른 PC에서 접속 시도
4. 실패하면 방화벽 및 포트 포워딩 확인

