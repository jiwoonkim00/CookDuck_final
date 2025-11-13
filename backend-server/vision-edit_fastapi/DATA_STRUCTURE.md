# 현재 데이터 구조

## 📊 전체 데이터 요약

- **총 레시피 수**: 537개
- **주재료 정보**: 537개 (100%)
- **부재료 정보**: 475개 (88%)
- **평균 재료 수**: 약 100자 (약 10-15개 재료)
- **평균 주재료 길이**: 약 71자
- **평균 부재료 길이**: 약 29자

## 🗄️ 데이터베이스 구조 (recipe_new 테이블)

```sql
CREATE TABLE recipe_new (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    title           TEXT NOT NULL,              -- 레시피 제목
    ingredients     TEXT,                       -- 전체 재료 (쉼표 구분)
    main_ingredients TEXT,                       -- 주재료 (쉼표 구분)
    sub_ingredients  TEXT,                       -- 부재료 (쉼표 구분)
    tools           TEXT,                       -- 도구/기구
    content         TEXT,                       -- 조리법 내용
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 📋 CSV 파일 구조

### 1. recipe_final.csv
```
레시피 코드 | 레시피 이름 | 재료명 | 재료수 | 요리설명 | 요약 | 유형분류 | 음식분류 | 조리시간 | 분량 | 난이도 | 재료별 분류명 | 가격별 분류
```

**주요 컬럼:**
- `레시피 코드`: 고유 ID
- `레시피 이름`: 레시피 제목
- `재료명`: 쉼표로 구분된 전체 재료 목록
- `요리설명`: 단계별 조리법

### 2. recipe_ingredient_cleaned.csv
```
레시피 코드 | 재료순번 | 재료명 | 재료용량 | 재료타입 코드 | 재료타입명
```

**주요 컬럼:**
- `레시피 코드`: 레시피 ID (recipe_final.csv와 연결)
- `재료명`: 개별 재료 이름
- `재료타입명`: "주재료" 또는 "부재료" 정보

## 📦 FAISS 인덱스 구조

### 인덱스 파일
- `faiss_store/index_new.faiss`: 벡터 인덱스 (1.6MB)
- `faiss_store/metadata_new.pkl`: 메타데이터 (425KB)

### 메타데이터 구조
```python
{
    "id": int,                    # 레시피 ID
    "title": str,                 # 레시피 제목
    "ingredients": str,           # 전체 재료 (쉼표 구분)
    "main_ingredients": str,      # 주재료 (쉼표 구분)
    "sub_ingredients": str,       # 부재료 (쉼표 구분)
    "content": str                # 조리법 내용
}
```

### 인덱스 정보
- **벡터 개수**: 537개
- **벡터 차원**: 768차원 (KR-SBERT 모델)
- **인덱스 타입**: IndexFlatL2 (L2 거리 기반)

## 🔄 데이터 처리 흐름

```
1. CSV 파일
   ├── recipe_final.csv (537개 레시피)
   └── recipe_ingredient_cleaned.csv (6095개 재료 정보)
        ↓
2. load_csv_to_new_table.py
   ├── 재료타입명으로 주재료/부재료 자동 분류
   └── recipe_new 테이블에 저장
        ↓
3. build_faiss_new_table.py
   ├── 주재료 강조 텍스트 생성
   ├── SentenceTransformer로 임베딩
   └── FAISS 인덱스 구축
        ↓
4. app/faiss_search_new.py
   ├── 주재료/부재료 가중치 적용
   └── 추천 결과 반환
```

## 📝 데이터 예시

### 예시 1: 나물비빔밥
```json
{
  "id": 1,
  "title": "나물비빔밥",
  "ingredients": "쌀,안심,콩나물,청포묵,미나리,소금,국간장,다진파,다진마늘,참기름,고추장,설탕,숙주,도라지,고사리,계란,양지머리",
  "main_ingredients": "쌀,안심,콩나물,청포묵,미나리,소금,국간장,다진파,다진마늘,참기름,설탕,숙주,도라지,고사리,계란",
  "sub_ingredients": "고추장,양지머리",
  "content": "1. 양지머리로 육수를 낸 후... (조리법)"
}
```

### 예시 2: 오곡밥
```json
{
  "id": 2,
  "title": "오곡밥",
  "ingredients": "멥쌀,찹쌀,수수,차조,콩,팥,소금",
  "main_ingredients": "멥쌀,찹쌀,소금",
  "sub_ingredients": "수수,차조,콩,팥"
}
```

## 🎯 주재료/부재료 분류 기준

### 주재료로 분류되는 경우
1. 레시피 제목에 포함된 재료
2. 고기류, 생선류, 해산물
3. 채소류 (주요 식재료)
4. 재료타입명이 "주재료"인 경우

### 부재료로 분류되는 경우
1. 조미료 (소금, 설탕, 간장, 된장, 고추장 등)
2. 식용유류
3. 기본 재료 (물, 마늘, 파, 양파 등)
4. 재료타입명이 "부재료" 또는 "조미료"인 경우

## 🔍 데이터 품질

- ✅ 주재료 정보: 100% 완성도
- ✅ 부재료 정보: 88% 완성도 (475/537)
- ✅ FAISS 인덱스: 완전히 구축됨
- ✅ 메타데이터 일치: 인덱스와 메타데이터 크기 일치 (537개)

