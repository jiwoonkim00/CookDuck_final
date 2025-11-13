FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치 (curl for healthcheck, SSH server, OpenGL for OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssh-server \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 파일 복사
COPY ./app /app/app
COPY ./vision_task /app/vision_task
COPY build_faiss.py .
COPY ./faiss_store /app/faiss_store

# SSH 및 헬스체크용 엔드포인트 노출
EXPOSE 8000 22

# SSH 초기화 스크립트 복사
COPY init-ssh.sh /usr/local/bin/init-ssh.sh
RUN chmod +x /usr/local/bin/init-ssh.sh

# SSH 설정 파일 복사
COPY sshd_config /etc/ssh/sshd_config

# 비전 모델 경로
ENV INGREDIENT_MODEL_PATH="/app/vision_task/model/veg_yolov8.pt"
# FastAPI와 SSH를 함께 실행
CMD ["sh", "-c", "/usr/local/bin/init-ssh.sh & uvicorn app.main:app --host 0.0.0.0 --port 8000"]
