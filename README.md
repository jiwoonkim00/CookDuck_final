
# 🥚 CookDuck – AI 기반 멀티모달 요리 도우미 앱

**CookDuck**은  
📸 *이미지로 재료를 인식하고*  
🧠 *RAG + LLM으로 레시피를 추천하며*  
🎙 *실시간 음성으로 조리 과정을 도와주는*  

**AI 기반 멀티모달 요리 도우미 서비스**입니다.

- 냉장고 속 재료 사진만 찍으면 → 만들 수 있는 요리를 추천해 주고  
- 요리 중에는 음성으로 “다음 단계 알려줘”, “다시 설명해줘” 라고 말하면  
  AI가 실시간으로 조리 과정을 안내합니다.

---

## 🚀 주요 기능 (Features)

### 1. 재료 이미지 자동 인식 (YOLOv8)
- 앱에서 카메라로 냉장고/식재료를 촬영하면 서버의 **YOLOv8** 모델이 재료를 자동 인식
- 인식된 재료를 **주재료 / 부재료**로 분류하여 레시피 추천에 활용
- 사용자는 재료를 직접 검색·입력할 필요 없이 바로 추천을 받을 수 있음

### 2. RAG 기반 레시피 추천 (Sentence-BERT + FAISS)
- 인식된 재료 목록을 문장으로 구성 후, **Sentence-BERT 임베딩**으로 벡터화
- **FAISS 벡터 DB**에서 의미적으로 가장 유사한 레시피 Top-K 검색
- 레시피별 **주재료/부재료 가중치**를 반영하여 실제로 만들기 좋은 레시피 순으로 재정렬
- LLM이 “이 레시피를 추천하는 이유”를 생성해 사용자에게 설명

### 3. 실시간 음성 요리 도우미 (STT → LLM → TTS)
- 앱과 서버는 **WebSocket**으로 연결되어 실시간 대화 가능
- 사용자의 음성은 **Whisper(STT)** 로 텍스트로 변환
- 레시피 정보 + 현재 단계 + 제약 조건을 포함해 **Llama 3.2 SFT**로 적절한 답변 생성
- **TTS**로 다시 음성으로 변환하여 조리 중 손을 쓰지 않고도 요리 가능
- 지원 예시:
  - `“다음 단계”` → 다음 조리 단계 안내  
  - `“처음부터 다시”` → 첫 단계부터 재안내  
  - `“매운맛 줄여줘”` → 제약 조건 반영하여 조리 방법 수정

### 4. 사용자 앱 기능 (Flutter)
- **북마크 / 즐겨찾기**  
  - 마음에 드는 레시피 저장
- **냉장고 관리**  
  - 보유 재료 저장 및 YOLO 인식 결과와 연동
- **요리 기록 / 캘린더**  
  - 언제 어떤 요리를 했는지 기록 관리
- **개인화 설정**  
  - 요리 실력, 선호 맛(맵기 등), 싫어하는 재료, 제약(비건/알레르기) 등 저장

---

## 🏗 시스템 아키텍처 (Architecture)

CookDuck은 **2대의 서버 + 1개의 모바일 앱** 구조로 동작합니다.

- 📱 **Flutter App**  
- 🖥 **Main Server (Server Computer)** – Spring Boot + FastAPI + DB + YOLO + FAISS  
- 🧠 **LLM Server (GPU Server)** – Whisper + Llama 3.2 SFT + TTS + LangChain

```text
[ Flutter App ]
    │ REST / WebSocket
    ▼
┌────────────────────── Main Server ───────────────────────┐
│ Nginx (선택)                                             │
│ Spring Boot  - 회원, 냉장고, 북마크, 요리 기록 관리     │
│ FastAPI      - /recommend, /vision, /ws/recipe-chat      │
│ YOLOv8       - 재료 이미지 인식                          │
│ MariaDB      - user, recipe, bookmark, fridge            │
│ FAISS        - 레시피 임베딩 벡터 인덱스                │
└──────────────────────────────────────────────────────────┘
                      │ HTTP
                      ▼
┌────────────────────── LLM Server (GPU) ──────────────────┐
│ Whisper STT   - 음성 → 텍스트                           │
│ Llama 3.2 SFT - 조리 단계 안내, 설명, 추천 이유 생성    │
│ MeloTTS       - 텍스트 → 음성                           │
│ LangChain     - RAG 파이프라인, 프롬프트/체인 구성      │
└──────────────────────────────────────────────────────────┘
```
🧩 기술 스택 (Tech Stack)
📱 Frontend (Mobile)

Flutter

Dart

WebSocket 통신

🖥 Backend (Main Server)

Spring Boot (Java/Kotlin)

FastAPI (Python)

MariaDB

SQLAlchemy / JPA

FAISS (Vector Search)

YOLOv8 (Object Detection)

🧠 LLM / AI Server

Python

Whisper (STT)

Llama 3.2 SFT (LLM)

MeloTTS (TTS)

Sentence-BERT / BGE (Embedding)

LangChain (RAG & Chain Orchestration)

📁 프로젝트 구조 예시 (Project Structure)

실제 폴더 구조에 맞게 수정해서 쓰면 됩니다.

cookduck/
├── backend-main/
│   ├── spring-api/           # 회원, 냉장고, 북마크, 캘린더 등
│   ├── fastapi-api/          # /recommend, /vision, /ws 등
│   ├── vision/               # YOLOv8 관련 코드
│   ├── db/                   # DB 초기 스크립트, 마이그레이션
│   └── README.md
├── llm-server/
│   ├── rag/                  # LangChain, RAG 파이프라인
│   ├── stt/                  # Whisper
│   ├── tts/                  # MeloTTS
│   ├── models/               # Llama 3.2 SFT 등
│   └── README.md
├── app-flutter/
│   ├── lib/
│   ├── android/
│   ├── ios/
│   └── README.md
└── README.md                 # (현재 이 파일)

⚙️ 설치 및 실행 (Setup & Run)

아래 내용도 실제 사용 환경에 맞게 포트/주소 수정해서 사용하세요.

1. 공통 요구사항 (Prerequisites)

Python 3.10+

Node.js/Flutter SDK 설치 (Flutter 앱용)

Java 17+ / Gradle (Spring Boot)

CUDA 지원 GPU (LLM 서버, 선택적)

2. Main Server 실행
cd backend-main

# FastAPI 서버 (예시)
cd fastapi-api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Spring Boot 서버 (예시)
cd ../spring-api
./gradlew bootRun

3. LLM Server 실행
cd llm-server
pip install -r requirements.txt

# 예시: STT/LLM/TTS 통합 서버
python main_llm_server.py

4. Flutter 앱 실행
cd app-flutter
flutter pub get
flutter run

🔄 동작 흐름 (How It Works)

재료 인식

사용자가 앱에서 사진 촬영 → Main Server로 이미지 전송 → YOLOv8이 재료 인식

레시피 추천

인식된 재료 → SBERT 임베딩 → FAISS 검색 → 주재료/부재료 가중치 → 상위 레시피 추천

실시간 음성 안내

WebSocket 연결 → 사용자 음성 → STT → LLM → TTS → 조리 단계 음성 안내

개인화

사용자 정보, 냉장고 상태, 요리 기록을 저장
→ 점점 더 개인화된 레시피 및 안내 제공

🌱 향후 확장 가능성

식재료 커머스 연동 (마켓컬리/쿠팡 API)

B2B API 제공 (식재료 인식/레시피 추천 엔진)

스마트 키친/냉장고/IoT 기기 연동

헬스케어/다이어트 앱과 연동한 식단 추천

📜 라이선스

필요 시 MIT / Apache-2.0 / GPL 등 프로젝트 성격에 맞는 라이선스를 추가하세요.

👨‍👩‍👧‍👦 팀 정보

프로젝트명: CookDuck – AI 기반 요리 도우미

참여 인원: 1조 (팀원 정보/역할 기재)

지도교수: (이름)
