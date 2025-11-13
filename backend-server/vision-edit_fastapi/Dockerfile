FROM python:3.10-slim

WORKDIR /app

# 시스템 라이브러리 및 파이썬 패키지 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

# CPU 버전 패키지 설치 (Apple Silicon M1 대응)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 파일 복사
COPY ./app /app/app
COPY ["./service", "/app/service"]
COPY build_faiss.py .
# faiss_store는 docker-compose.yml에서 볼륨 마운트로 제공됨
RUN mkdir -p /app/faiss_store

ENV INGREDIENT_MODEL_PATH="/app/service/model/veg_yolov8.pt"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
