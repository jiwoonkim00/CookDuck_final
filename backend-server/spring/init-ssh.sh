#!/bin/sh
set -e

# SSH 서버 설정
mkdir -p /var/run/sshd
chmod 755 /var/run/sshd

# root 비밀번호 설정 (환경 변수에서 가져오거나 기본값 사용)
ROOT_PASSWORD=${SSH_ROOT_PASSWORD:-root123}
echo "root:$ROOT_PASSWORD" | chpasswd

# SSH 설정
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
echo "Port 22" >> /etc/ssh/sshd_config

# SSH 서버를 백그라운드로 시작
/usr/sbin/sshd -D &

