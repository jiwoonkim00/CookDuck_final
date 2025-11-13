# 주재료/부재료 가중치 기반 추천 시스템

## 📋 개요

기존 24만개 데이터를 벡터 DB와 MariaDB에 저장하여 추천하던 시스템을 개선하여, **주재료와 부재료를 구분**하고 **주재료 매칭에 가중치를 적용**하여 더 정확한 추천을 제공합니다.

## 🎯 주요 기능

1. **주재료/부재료 자동 분류**
   - 레시피 제목에 포함된 재료 → 주재료
   - 조미료, 식용유, 물 등 기본 재료 → 부재료
   - 고기, 채소, 해산물 등 주요 식재료 → 주재료

2. **가중치 적용 추천**
   - 주재료 매칭: 2.0배 가중치 (기본값)
   - 부재료 매칭: 1.0배 가중치
   - 주재료 매칭이 우선적으로 반영됨

3. **향상된 정확도**
   - 주재료가 일치하는 레시피가 우선적으로 추천됨
   - 부재료만 일치하는 레시피는 낮은 순위

## 📁 파일 구조

```
backend-server/fastapi/
├── add_ingredient_columns.sql        # DB 스키마 업데이트 SQL
├── load_csv_with_main_sub.py        # CSV 데이터 로더 (주재료/부재료 구분)
├── app/
│   ├── faiss_search_weighted.py      # 가중치 기반 추천 알고리즘
│   ├── api.py                        # API 엔드포인트 (가중치 지원)
│   └── faiss_search.py               # 기존 추천 알고리즘 (폴백용)
└── build_faiss.py                    # FAISS 인덱스 구축 (주재료 강조)
```

## 🚀 사용 방법

### 1. 데이터베이스 스키마 업데이트

```bash
# MariaDB 컨테이너에서 실행
docker-compose exec mariadb mysql -uroot -proot recipe_db < add_ingredient_columns.sql

# 또는 직접 실행
cd backend-server/fastapi
docker-compose exec mariadb mysql -uroot -proot recipe_db -e "ALTER TABLE recipe ADD COLUMN IF NOT EXISTS main_ingredients TEXT, ADD COLUMN IF NOT EXISTS sub_ingredients TEXT;"
```

### 2. CSV 데이터 로드

```bash
cd backend-server/fastapi

# CSV 파일 경로 지정하여 실행
python load_csv_with_main_sub.py \
  ~/Downloads/data/recipe_final.csv \
  ~/Downloads/data/recipe_ingredient_cleaned.csv
```

**CSV 파일 구조 예시:**

`recipe_final.csv`:
```csv
id,title,content,...
1,김치볶음밥,조리법...
```

`recipe_ingredient_cleaned.csv`:
```csv
recipe_id,ingredient_name,is_main,...
1,김치,true
1,밥,true
1,계란,true
1,소금,false
```

### 3. FAISS 인덱스 재구축 (주재료 강조)

```bash
cd backend-server/fastapi

# 가상환경 활성화
source venv/bin/activate

# FAISS 인덱스 재구축 (주재료를 강조한 임베딩)
python build_faiss.py
```

### 4. API 테스트

#### 기본 사용 (자동 분류)
```bash
curl -X POST http://localhost:81/api/fastapi/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["김치", "계란", "밥", "소금"]
  }'
```

#### 주재료/부재료 명시
```bash
curl -X POST http://localhost:81/api/fastapi/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["김치", "계란", "밥", "소금"],
    "main_ingredients": ["김치", "계란", "밥"],
    "sub_ingredients": ["소금"],
    "main_weight": 2.5
  }'
```

#### 가중치 기반 엔드포인트 (명시적)
```bash
curl -X POST http://localhost:81/api/fastapi/recommend/weighted \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["돼지고기", "양파", "고추장"],
    "main_ingredients": ["돼지고기", "양파"],
    "sub_ingredients": ["고추장"],
    "main_weight": 3.0
  }'
```

## 🔧 알고리즘 설명

### 점수 계산 방식

```python
# 주재료 점수 = (매칭된 주재료 수 / 사용자 주재료 수) × 주재료 가중치
main_score = (matched_main / user_main) × 2.0

# 부재료 점수 = (매칭된 부재료 수 / 사용자 부재료 수) × 부재료 가중치
sub_score = (matched_sub / user_sub) × 1.0

# 가중치 적용 매칭 점수
weighted_match_score = (main_score + sub_score) / (main_weight + sub_weight)

# 최종 점수 (주재료 매칭 우선)
if matched_main:
    final_score = 0.2 × dist_score + 0.8 × weighted_match_score
else:
    final_score = 0.4 × dist_score + 0.6 × simple_match_score
```

### 정렬 기준

1. **주재료 매칭 수** (우선)
2. **최종 점수** (차순위)

## 📊 응답 형식

```json
[
  {
    "id": 123,
    "title": "김치볶음밥",
    "ingredients": "김치,밥,계란,소금",
    "main_ingredients": "김치,밥,계란",
    "sub_ingredients": "소금",
    "content": "조리법...",
    "score": 0.85,
    "match_score": 0.82,
    "matched_main_ingredients": ["김치", "밥", "계란"],
    "matched_sub_ingredients": ["소금"],
    "matched_ingredients": ["김치", "밥", "계란", "소금"],
    "distance": 0.23
  }
]
```

## ⚙️ 설정 조정

### 주재료 가중치 변경

`main_weight` 파라미터로 조정 가능:
- `2.0`: 기본값 (주재료 2배 가중치)
- `3.0`: 주재료 3배 가중치 (더 강하게)
- `1.5`: 주재료 1.5배 가중치 (덜 강하게)

## 🔄 마이그레이션 가이드

### 기존 데이터 마이그레이션

기존 24만개 데이터에 주재료/부재료를 자동으로 분류하려면:

1. CSV 파일이 없을 경우, 기존 `ingredients` 컬럼에서 자동 분류:
   - 스크립트가 조미료 키워드를 기반으로 자동 분류

2. CSV 파일이 있을 경우:
   - `load_csv_with_main_sub.py` 실행하여 정확한 분류 적용

## 🐛 문제 해결

### 주재료/부재료가 구분되지 않는 경우

1. CSV 파일의 컬럼명 확인
2. `load_csv_with_main_sub.py`의 컬럼 매핑 수정
3. 재료 분류 로직 (`classify_main_sub`) 커스터마이징

### 추천 결과가 기대와 다른 경우

1. `main_weight` 값 조정 (2.0 → 3.0 등)
2. 주재료 분류 기준 수정 (`classify_main_sub` 함수)
3. 최소 매칭 임계값 조정 (`match_score < 0.1` 부분)

