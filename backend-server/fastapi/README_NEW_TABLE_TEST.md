# recipe_new 테이블 테스트 가이드

## 📋 개요

기존 24만개 데이터(`recipe` 테이블)와 분리된 새로운 테이블(`recipe_new`)을 생성하여 주재료/부재료 가중치 기반 추천 시스템을 테스트할 수 있습니다.

## 🚀 사용 절차

### 1단계: 새 테이블 생성

```bash
cd backend-server/fastapi

# MariaDB에서 새 테이블 생성
docker-compose exec mariadb mysql -uroot -proot recipe_db < create_recipe_new_table.sql

# 또는 직접 실행
docker-compose exec mariadb mysql -uroot -proot recipe_db -e "CREATE TABLE IF NOT EXISTS recipe_new (...)"
```

### 2단계: CSV 데이터 로드

```bash
# 가상환경 활성화 (필요시)
source venv/bin/activate

# CSV 파일 경로 지정하여 실행
python load_csv_to_new_table.py \
  /Users/kimjiwoon/Downloads/data/recipe_final.csv \
  /Users/kimjiwoon/Downloads/data/recipe_ingredient_cleaned.csv
```

**옵션:**
- 재료 파일이 없으면 레시피 파일의 `ingredients` 컬럼을 사용
- 자동으로 주재료/부재료 분류

### 3단계: FAISS 인덱스 구축

```bash
# recipe_new 테이블용 FAISS 인덱스 구축
python build_faiss_new_table.py
```

**인덱스 저장 위치:**
- 인덱스: `faiss_store/index_new.faiss`
- 메타데이터: `faiss_store/metadata_new.pkl`

### 4단계: API 테스트

```bash
# recipe_new 테이블 기반 추천
curl -X POST http://localhost:81/api/fastapi/recommend/new \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["김치", "계란", "밥", "소금"]
  }'

# 주재료/부재료 명시
curl -X POST http://localhost:81/api/fastapi/recommend/new \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["돼지고기", "양파", "고추장"],
    "main_ingredients": ["돼지고기", "양파"],
    "sub_ingredients": ["고추장"],
    "main_weight": 2.5
  }'
```

## 📊 테이블 비교

| 항목 | recipe (기존) | recipe_new (새 테이블) |
|------|--------------|----------------------|
| 데이터 수 | 24만개 | CSV 파일 기반 (사용자 데이터) |
| FAISS 인덱스 | `index.faiss` | `index_new.faiss` |
| API 엔드포인트 | `/recommend` | `/recommend/new` |
| 주재료/부재료 | 지원 | 지원 (CSV에서 로드) |

## 🔍 데이터 확인

### 테이블 데이터 확인

```bash
# recipe_new 테이블 데이터 수 확인
docker-compose exec mariadb mysql -uroot -proot recipe_db \
  -e "SELECT COUNT(*) as total FROM recipe_new;"

# 주재료/부재료 통계
docker-compose exec mariadb mysql -uroot -proot recipe_db \
  -e "SELECT 
      COUNT(*) as total,
      SUM(CASE WHEN main_ingredients IS NOT NULL AND main_ingredients != '' THEN 1 ELSE 0 END) as with_main,
      SUM(CASE WHEN sub_ingredients IS NOT NULL AND sub_ingredients != '' THEN 1 ELSE 0 END) as with_sub
    FROM recipe_new;"
```

### FAISS 인덱스 확인

```python
import faiss
import pickle

# 인덱스 로드
index = faiss.read_index("faiss_store/index_new.faiss")
with open("faiss_store/metadata_new.pkl", "rb") as f:
    metadata = pickle.load(f)

print(f"인덱스 크기: {index.ntotal}개")
print(f"메타데이터 크기: {len(metadata)}개")
```

## 🛠️ 문제 해결

### 1. 인덱스 로드 오류

```
⚠️ recipe_new 인덱스 로드 실패: [Errno 2] No such file or directory
```

**해결:** `build_faiss_new_table.py` 실행하여 인덱스 구축

### 2. 테이블이 비어있음

```
❌ recipe_new 테이블에 데이터가 없습니다.
```

**해결:** `load_csv_to_new_table.py` 실행하여 데이터 로드

### 3. CSV 컬럼 매핑 오류

스크립트가 자동으로 컬럼을 감지하지만, 수동으로 수정해야 할 경우:

`load_csv_to_new_table.py`의 `find_column` 함수 또는 직접 컬럼명 지정

## 📝 예제 시나리오

### 시나리오 1: 소규모 데이터 테스트

```bash
# 1. 작은 CSV 파일 준비 (예: 100개 레시피)
# 2. 테이블 생성
docker-compose exec mariadb mysql -uroot -proot recipe_db < create_recipe_new_table.sql

# 3. 데이터 로드
python load_csv_to_new_table.py small_recipe_test.csv

# 4. 인덱스 구축
python build_faiss_new_table.py

# 5. API 테스트
curl -X POST http://localhost:81/api/fastapi/recommend/new \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["김치", "밥"]}'
```

### 시나리오 2: 기존 데이터와 비교

```bash
# recipe 테이블 추천 (24만개 데이터)
curl -X POST http://localhost:81/api/fastapi/recommend \
  -d '{"ingredients": ["김치", "계란"]}'

# recipe_new 테이블 추천 (새 데이터)
curl -X POST http://localhost:81/api/fastapi/recommend/new \
  -d '{"ingredients": ["김치", "계란"]}'

# 결과 비교
```

## 🗑️ 데이터 초기화

```bash
# recipe_new 테이블 데이터 삭제
docker-compose exec mariadb mysql -uroot -proot recipe_db \
  -e "TRUNCATE TABLE recipe_new;"

# FAISS 인덱스 삭제
rm faiss_store/index_new.faiss faiss_store/metadata_new.pkl faiss_store/last_processed_new.txt
```

## 📚 관련 파일

- `create_recipe_new_table.sql` - 새 테이블 생성 SQL
- `load_csv_to_new_table.py` - CSV 데이터 로더
- `build_faiss_new_table.py` - FAISS 인덱스 구축
- `app/faiss_search_new.py` - 새 테이블용 추천 알고리즘

