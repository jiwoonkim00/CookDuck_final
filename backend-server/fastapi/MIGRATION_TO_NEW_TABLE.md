# recipe_new 테이블로 마이그레이션 완료

## ✅ 변경 사항

이제 **recipe_new 테이블**이 기본 데이터 소스로 사용됩니다.

### 주요 변경점

1. **기본 추천 엔드포인트 변경**
   - `/recommend` → recipe_new 테이블 사용 (주재료/부재료 가중치 적용)
   - 이전: 기존 recipe 테이블 (24만개 데이터)
   - 현재: recipe_new 테이블 (537개 신규 데이터)

2. **엔드포인트 정리**
   - `/recommend` - **기본 추천** (recipe_new 테이블, 주재료/부재료 가중치)
   - `/recommend/new` - **별칭** (동일하게 recipe_new 테이블 사용)
   - `/recommend/weighted` - **명시적 가중치 추천** (recipe_new 테이블)
   - `/recommend/legacy` - **레거시** (기존 recipe 테이블, 호환성 유지)
   - `/recommend/rag` - **RAG 추천** (레거시, 호환성 유지)

## 📊 데이터 소스 비교

| 항목 | recipe (기존) | recipe_new (새 테이블) |
|------|--------------|----------------------|
| 레시피 수 | 24만개 | 537개 |
| 주재료 정보 | 없음/부분 | 있음 (100%) |
| 부재료 정보 | 없음/부분 | 있음 (88%) |
| FAISS 인덱스 | index.faiss | index_new.faiss |
| 기본 엔드포인트 | `/recommend` (이전) | `/recommend` (현재) |

## 🔄 사용 예시

### 기본 추천 (recipe_new 테이블)
```bash
curl -X POST http://localhost:81/api/fastapi/recommend \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["김치", "계란", "밥"]}'
```

### 주재료/부재료 명시
```bash
curl -X POST http://localhost:81/api/fastapi/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["돼지고기", "양파", "고추장"],
    "main_ingredients": ["돼지고기", "양파"],
    "sub_ingredients": ["고추장"],
    "main_weight": 2.5
  }'
```

### 레거시 엔드포인트 (기존 recipe 테이블)
```bash
curl -X POST http://localhost:81/api/fastapi/recommend/legacy \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["김치", "계란"]}'
```

## ⚠️ 주의사항

- 기존 recipe 테이블 데이터는 `/recommend/legacy`로만 접근 가능
- 모든 기본 추천은 이제 recipe_new 테이블 사용
- 주재료/부재료 가중치가 자동으로 적용됨

## 🔧 설정 변경

- `app/api.py`: 기본 엔드포인트가 `recommend_recipes_new_table()` 사용
- `app/faiss_search_new.py`: recipe_new 테이블 전용 추천 함수
- `faiss_store/index_new.faiss`: 새로운 FAISS 인덱스

## 📝 다음 단계

1. 프론트엔드 API 호출 확인
2. 추천 결과 품질 검증
3. 필요시 데이터 추가 (recipe_new 테이블 확장)

