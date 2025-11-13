# 🍳 CookDuck 시스템 아키텍처 및 기능 로직 정리

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [전체 플로우](#전체-플로우)
3. [주요 기능별 상세 로직](#주요-기능별-상세-로직)
4. [데이터베이스 구조](#데이터베이스-구조)
5. [API 엔드포인트 정리](#api-엔드포인트-정리)
6. [기술 스택](#기술-스택)

---

## 시스템 개요

CookDuck은 AI 기반 요리 도우미 애플리케이션으로, 다음과 같은 기능을 제공합니다:

- 📸 **이미지 기반 재료 인식**: YOLO + VLM으로 사진에서 재료 자동 인식
- 🗄️ **재료 관리**: 인식된 재료를 DB에 저장하고 냉장고 페이지에서 관리
- 🔍 **레시피 추천**: FAISS 벡터 검색으로 보유 재료 기반 레시피 추천
- 🎤 **음성 요리 가이드**: WebSocket 기반 실시간 음성 대화로 단계별 요리 안내
- 🎯 **맞춤화 기능**: 사용자 제약사항(매운맛, 저염 등) 동적 감지 및 레시피 수정

---

## 전체 플로우

### 1️⃣ 레시피 검색 플로우 (RAG - Search)

```
[사용자] 사진 촬영
    ↓
[Flutter] take_picture_screen.dart
    ↓
[1] 조미료 조회: GET /api/user-seasonings/{userId}
    ↓
[2] 이미지 분석: POST /api/fastapi/predict
    ├─ YOLO: 초기 재료 검출 (영어)
    └─ VLM: 한국어 번역 + 추가 검출
    ↓
[3] 재료 분류: 주재료/부재료 구분
    ├─ 주재료: 고기, 채소 등
    └─ 부재료: 조미료 + 인식된 조미료 재료
    ↓
[4] 재료 DB 저장: POST /api/user-ingredients/{userId}
    ├─ 기존 재료 삭제
    └─ 새 재료 저장 (주재료/부재료 구분)
    ↓
[5] 레시피 추천: POST /api/recommend
    ├─ Spring Boot: 요청 전달
    ├─ FastAPI: FAISS 벡터 검색
    │   ├─ 재료 임베딩 생성 (SentenceTransformer)
    │   ├─ FAISS 유사도 검색
    │   └─ 가중치 점수 계산 (주재료 2배, 부재료 1배)
    └─ 레시피 목록 반환
    ↓
[6] 결과 화면: RecipeResultScreen
    ├─ 보유 조미료 표시
    ├─ 보유 식재료 표시
    └─ 추천 레시피 카드 목록
```

### 2️⃣ 대화 시작 플로우 (Conversation Start)

```
[사용자] 레시피 선택
    ↓
[Flutter] 레시피 상세 화면에서 "요리 시작" 버튼 클릭
    ↓
[1] 레시피 세션 생성: POST /api/fastapi/cook/select
    ├─ user_id, recipe_id 전달
    ├─ 세션 생성 (CookSessionManager)
    └─ 레시피 데이터 로드 (DB에서)
    ↓
[2] WebSocket 연결: WS /api/fastapi/ws/chat?user_id={userId}&recipe_id={recipeId}
    ↓
[3] 초기 인사말 생성 (RAG 프롬프트)
    ├─ 레시피 정보 로드
    ├─ create_system_prompt() 호출
    │   ├─ 레시피 제목, 재료, 단계 포함
    │   └─ 제약사항 반영 (있는 경우)
    ├─ build_llama3_2_prompt() 호출
    │   └─ Llama 3.2 형식 프롬프트 생성
    ├─ ai서버 /llm-generate 호출
    └─ TTS 변환 후 음성 전송
    ↓
[사용자] "안녕하세요" 또는 "시작해주세요"
    ↓
[AI] "안녕하세요 쿡덕입니다! [레시피명]을 차근차근 안내해드리겠습니다"
```

### 3️⃣ 단계별 음성 안내 플로우 (Step-by-step Voice Guidance)

```
[사용자] "다음" (음성)
    ↓
[WebSocket] STT: POST /stt
    └─ 음성 → 텍스트 변환
    ↓
[1] 제약사항 감지 (ConstraintParser)
    ├─ "매운걸 잘 못먹어요" → spice_level decrease
    ├─ "저염으로" → low_salt decrease
    └─ 세션에 제약사항 추가
    ↓
[2] 단계 프롬프트 생성
    ├─ 현재 단계 인덱스 확인
    ├─ create_step_prompt() 호출
    │   ├─ 레시피 전체 단계 포함
    │   ├─ 현재 단계 정보
    │   └─ 제약사항 반영
    ├─ build_llama3_2_prompt() 호출
    └─ 최종 프롬프트 생성
    ↓
[3] LLM 응답 생성
    ├─ ai서버 /llm-generate 호출
    ├─ 제약사항 반영된 단계 안내 생성
    └─ 예: "1. 양지머리로 육수를 낸 후... (고추장은 50% 정도만 사용하세요)"
    ↓
[4] TTS 변환 및 전송
    ├─ ai서버 /tts 호출
    └─ 음성 스트리밍
    ↓
[5] 다음 단계로 이동
    └─ session.current_step += 1
```

---

## 주요 기능별 상세 로직

### 📸 이미지 기반 재료 인식

**파일**: `backend-server/vision-edit_fastapi/`

**프로세스**:
1. **YOLO 검출** (`yolo_service.py`)
   - 이미지에서 재료 객체 검출
   - 영어 클래스명 반환 (예: "onion", "garlic")

2. **VLM 번역 및 추가 검출** (`gptVlm_service.py`)
   - YOLO 결과를 VLM에 전달
   - 한국어로 번역 (예: "양파", "마늘")
   - YOLO가 놓친 재료 추가 검출

3. **결과 반환** (`fusion_service.py`)
   - 최종 한국어 재료 리스트 반환

**API**: `POST /api/fastapi/predict`

---

### 🗄️ 재료 저장 및 관리

**데이터베이스**: `user_ingredients` 테이블

**구조**:
```sql
CREATE TABLE user_ingredients (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    ingredient VARCHAR(255) NOT NULL,
    ingredient_type VARCHAR(50) NOT NULL, -- 'main' or 'sub'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**저장 로직**:
1. 사진 촬영 후 재료 인식
2. 주재료/부재료 자동 분류
   - 키워드 기반 분류 (소금, 설탕, 간장 등 → 부재료)
   - 나머지 → 주재료
3. 기존 재료 삭제 후 새 재료 저장

**API**:
- `POST /api/user-ingredients/{userId}` - 재료 저장
- `GET /api/user-ingredients/{userId}` - 재료 조회
- `DELETE /api/user-ingredients/{userId}` - 재료 삭제

**냉장고 페이지**: `frontend/lib/main_pages/myrefrig.dart`
- 저장된 재료를 주재료/부재료 구분하여 표시

---

### 🔍 레시피 추천 시스템

**기술**: FAISS 벡터 검색 + SentenceTransformer

**프로세스**:

1. **FAISS 인덱스 구축** (`build_faiss_new_table.py`)
   - `recipe_new` 테이블에서 레시피 로드
   - 각 레시피의 재료를 임베딩 벡터로 변환
   - FAISS 인덱스 생성 및 저장

2. **사용자 재료 임베딩** (`faiss_search_new.py`)
   - 사용자 보유 재료 리스트를 임베딩 벡터로 변환
   - 주재료와 부재료 구분

3. **유사도 검색**
   - FAISS로 유사한 레시피 검색 (top_k=500)
   - 가중치 점수 계산:
     ```
     score = (주재료 매칭 수 × 2.0) + (부재료 매칭 수 × 1.0) - distance
     ```

4. **결과 반환**
   - 점수 순으로 정렬
   - 상위 레시피 반환

**API**: `POST /api/recommend`
- Spring Boot → FastAPI 전달
- `main_ingredients`, `sub_ingredients` 포함

---

### 🎤 음성 요리 가이드 (WebSocket)

**기술**: WebSocket + RAG 프롬프트 + LLM

**WebSocket 엔드포인트**: `WS /api/fastapi/ws/chat?user_id={userId}&recipe_id={recipeId}`

**프로세스**:

1. **연결 및 초기화**
   - WebSocket 연결 수락
   - 레시피 정보 로드 (recipe_id가 있는 경우)
   - 세션 생성 (CookSessionManager)

2. **초기 인사말**
   - RAG 프롬프트 생성 (`create_system_prompt`)
   - Llama 3.2 형식 프롬프트 생성
   - ai서버 `/llm-generate` 호출
   - TTS 변환 및 전송

3. **대화 루프**
   ```
   while True:
       # 1. 사용자 음성 수신
       wav_data = await websocket.receive_bytes()
       
       # 2. STT (음성 → 텍스트)
       user_text = await stt(wav_data)
       
       # 3. 제약사항 감지
       constraints = constraint_parser.parse_message(user_text)
       if constraints:
           session.add_constraints(constraints)
       
       # 4. 프롬프트 생성
       if user_text == "다음":
           # 단계별 안내
           prompt = create_step_prompt(recipe, step_index, constraints)
       else:
           # 일반 대화
           prompt = create_system_prompt(recipe, constraints)
       
       # 5. LLM 응답 생성
       bot_response = await llm_generate(prompt)
       
       # 6. TTS 변환 및 전송
       audio = await tts(bot_response)
       await websocket.send_bytes(audio)
   ```

---

### 🎯 사용자 맞춤화 (제약사항 반영)

**제약사항 감지**: `ConstraintParser` (`cook_session.py`)

**지원하는 제약사항**:

1. **매운맛 조절**
   - 키워드: "매운걸 잘 못먹어", "덜 매운", "안 매운"
   - 타입: `spice_level`
   - 액션: `decrease` (light/medium/strong)

2. **짠맛 조절**
   - 키워드: "저염", "덜 짜게", "소금 적게"
   - 타입: `low_salt`
   - 액션: `decrease`

3. **기름 조절**
   - 키워드: "기름 적게", "저지방"
   - 타입: `oil`
   - 액션: `decrease`

4. **비건/채식**
   - 키워드: "비건", "채식", "고기 없이"
   - 타입: `vegan`
   - 액션: `enforce`

5. **알레르기**
   - 키워드: "견과류", "우유", "달걀" 등
   - 타입: `allergy`
   - 액션: `remove`

6. **건강 관련**
   - 저칼로리, 저당, 저콜레스테롤

7. **조리법**
   - 튀김 없이, 볶음, 찜 등

**프롬프트 반영**:
- `create_system_prompt()`: 제약사항을 자연어로 변환하여 프롬프트에 포함
- `create_step_prompt()`: 단계별 안내 시 제약사항 반영

**예시**:
```
사용자: "매운걸 잘 못먹어요"
→ 제약사항 감지: spice_level decrease medium
→ 프롬프트: "매운맛을 적당히 줄여주세요"
→ LLM 응답: "고추장은 50% 정도만 사용하세요"
```

---

## 데이터베이스 구조

### 주요 테이블

1. **recipe_new** (레시피 정보)
   - `id`, `title`, `ingredients`, `main_ingredients`, `sub_ingredients`, `content`

2. **user_ingredients** (사용자 재료)
   - `id`, `user_id`, `ingredient`, `ingredient_type` (main/sub)

3. **user_seasoning_pivot** (사용자 조미료)
   - `user_id`, `간장`, `된장`, `고추장`, `소금`, `후추`, `설탕`, `고춧가루`, `식초`, `참기름`

4. **users** (사용자 정보)
   - `id`, `userId`, `email`, `password`, `name`, `grade`

---

## API 엔드포인트 정리

### Spring Boot (포트 8080)

**재료 관리**:
- `GET /api/user-seasonings/{userId}` - 조미료 조회
- `POST /api/user-seasonings/{userId}` - 조미료 저장
- `GET /api/user-ingredients/{userId}` - 재료 조회
- `POST /api/user-ingredients/{userId}` - 재료 저장
- `DELETE /api/user-ingredients/{userId}` - 재료 삭제

**레시피 추천**:
- `POST /api/recommend` - 레시피 추천 (FastAPI로 전달)

### FastAPI (포트 8000)

**이미지 분석**:
- `POST /api/fastapi/predict` - 재료 인식 (YOLO + VLM)

**레시피 추천**:
- `POST /api/fastapi/recommend` - FAISS 벡터 검색
- `POST /api/fastapi/recommend/rag` - RAG 기반 추천

**요리 세션**:
- `POST /api/fastapi/cook/select` - 레시피 선택 및 세션 생성
- `POST /api/fastapi/cook/next` - 다음 단계 이동
- `GET /api/fastapi/cook/current` - 현재 단계 조회
- `POST /api/fastapi/cook/constraint` - 제약사항 추가
- `DELETE /api/fastapi/cook/session/{user_id}` - 세션 삭제

**WebSocket**:
- `WS /api/fastapi/ws/chat?user_id={userId}&recipe_id={recipeId}` - 음성 채팅

### AI 서버 (포트 8001)

- `POST /stt` - 음성 → 텍스트
- `POST /tts` - 텍스트 → 음성
- `POST /llm-generate` - LLM 응답 생성
- `POST /generate-greeting` - 인사말 생성
- `POST /generate-llm-response` - LLM 응답 생성

---

## 기술 스택

### 백엔드
- **Spring Boot**: 사용자 관리, 재료 저장, API 게이트웨이
- **FastAPI**: AI/ML 서비스 (레시피 추천, 이미지 분석)
- **MariaDB**: 데이터베이스
- **FAISS**: 벡터 검색 엔진
- **SentenceTransformer**: 텍스트 임베딩

### AI/ML
- **YOLO**: 객체 검출 (재료 인식)
- **GPT VLM**: 이미지 분석 및 번역
- **Llama 3.2**: 대화형 요리 가이드
- **RAG (Retrieval-Augmented Generation)**: 레시피 기반 프롬프트 생성

### 프론트엔드
- **Flutter**: 크로스 플랫폼 모바일 앱
- **WebSocket**: 실시간 음성 통신

### 인프라
- **Docker Compose**: 멀티 컨테이너 오케스트레이션
- **Nginx**: 리버스 프록시 및 라우팅

---

## 주요 파일 구조

### 백엔드
```
backend-server/
├── spring/                    # Spring Boot 서버
│   └── src/main/java/com/api/
│       ├── controller/        # API 컨트롤러
│       ├── service/          # 비즈니스 로직
│       ├── entity/           # JPA 엔티티
│       └── repository/       # 데이터 접근
│
├── fastapi/                   # FastAPI 서버
│   └── app/
│       ├── api.py            # API 엔드포인트
│       ├── cook_api.py       # 요리 세션 API
│       ├── faiss_search_new.py  # FAISS 검색
│       ├── rag_prompt_builder.py # RAG 프롬프트
│       └── cook_session.py   # 세션 관리
│
└── vision-edit_fastapi/      # Vision 서버
    └── service/
        ├── yolo_service.py   # YOLO 검출
        ├── gptVlm_service.py  # VLM 분석
        └── fusion_service.py # 통합 파이프라인
```

### 프론트엔드
```
frontend/lib/
├── main_pages/
│   ├── take_picture_screen.dart    # 사진 촬영 및 재료 인식
│   ├── recipe_result_screen.dart   # 레시피 결과 화면
│   └── myrefrig.dart               # 냉장고 페이지
└── models/
    └── recipe.dart                 # 레시피 모델
```

---

## 데이터 흐름 다이어그램

```
[사용자]
    ↓
[Flutter 앱]
    ├─→ [Spring Boot] → [MariaDB] (재료 저장)
    ├─→ [FastAPI] → [FAISS] (레시피 검색)
    ├─→ [Vision API] → [YOLO + VLM] (재료 인식)
    └─→ [WebSocket] → [FastAPI] → [AI 서버] (음성 가이드)
```

---

## 향후 개선 사항

1. **재료 관리 개선**
   - 재료 수동 추가/삭제 기능
   - 재료 유통기한 관리
   - 재료 카테고리별 분류

2. **레시피 추천 개선**
   - 사용자 선호도 학습
   - 협업 필터링 추가
   - 실시간 재료 소진 반영

3. **음성 가이드 개선**
   - 대화 기록 저장
   - 중단 지점 저장 및 재개
   - 다국어 지원

4. **성능 최적화**
   - FAISS 인덱스 캐싱
   - 이미지 분석 결과 캐싱
   - WebSocket 연결 풀 관리

---

**최종 업데이트**: 2024년
**버전**: 1.0.0

