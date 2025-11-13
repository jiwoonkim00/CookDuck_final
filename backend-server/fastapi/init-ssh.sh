#!/bin/bash
set -e

# SSH 서버 설정
mkdir -p /var/run/sshd
chmod 755 /var/run/sshd

# root 비밀번호 설정 (환경 변수에서 가져오거나 기본값 사용)
ROOT_PASSWORD=${SSH_ROOT_PASSWORD:-root123}
echo "root:$ROOT_PASSWORD" | chpasswd

# SSH 호스트 키 생성 (없는 경우)
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# SSH 서버를 백그라운드로 시작
/usr/sbin/sshd -D &

