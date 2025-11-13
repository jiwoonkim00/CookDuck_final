"""
CSV 파일에서 주재료/부재료를 구분하여 MariaDB에 저장하는 스크립트
recipe_final.csv와 recipe_ingredient_cleaned.csv를 사용
"""

import pandas as pd
import pymysql
import os
from typing import Dict, List, Tuple
import re

# DB 연결 설정
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3307,
    'user': 'root',
    'password': 'root',
    'db': 'recipe_db',
    'charset': 'utf8mb4'
}

def clean_ingredient(ingredient: str) -> str:
    """재료명 정제 (숫자, 단위, 특수문자 제거)"""
    if pd.isna(ingredient) or not ingredient:
        return ""
    # 공백 제거 및 기본 정제
    cleaned = str(ingredient).strip()
    return cleaned

def classify_main_sub(ingredient: str, recipe_title: str = "") -> Tuple[bool, str]:
    """
    재료를 주재료/부재료로 분류
    주재료 판단 기준:
    1. 레시피 제목에 포함된 재료
    2. 고기류, 생선류, 해산물, 채소류 등 주요 식재료
    3. 부재료: 조미료, 식용유, 물, 소금 등 기본 재료
    """
    if not ingredient:
        return False, ""
    
    cleaned = clean_ingredient(ingredient)
    
    # 부재료 목록 (조미료, 기본 재료)
    sub_ingredients_keywords = [
        '소금', '설탕', '후추', '간장', '된장', '고추장', '식초', '참기름', '들기름',
        '식용유', '올리브유', '포도씨유', '카놀라유', '물', '다시마', '멸치', '미림',
        '맛술', '청주', '고춧가루', '마늘', '파', '양파', '생강', '미원', 'MSG',
        '녹말', '전분', '부침가루', '밀가루'
    ]
    
    # 제목에 포함되어 있으면 주재료
    if recipe_title and cleaned in recipe_title:
        return True, cleaned
    
    # 부재료 키워드 체크
    for keyword in sub_ingredients_keywords:
        if keyword in cleaned:
            return False, cleaned
    
    # 기본적으로 주재료로 간주 (고기, 채소, 해산물 등)
    return True, cleaned

def load_and_process_csv(
    recipe_file: str,
    ingredient_file: str,
    batch_size: int = 1000
) -> None:
    """
    CSV 파일을 읽어서 주재료/부재료를 구분하여 DB에 저장
    """
    print(f"📖 CSV 파일 로딩 중...")
    print(f"  - 레시피 파일: {recipe_file}")
    print(f"  - 재료 파일: {ingredient_file}")
    
    # CSV 파일 읽기
    try:
        df_recipes = pd.read_csv(recipe_file, encoding='utf-8')
        df_ingredients = pd.read_csv(ingredient_file, encoding='utf-8')
        print(f"✅ 레시피 데이터: {len(df_recipes)}개")
        print(f"✅ 재료 데이터: {len(df_ingredients)}개")
    except Exception as e:
        print(f"❌ CSV 파일 읽기 실패: {e}")
        print("\n💡 사용법:")
        print("   python load_csv_with_main_sub.py <recipe_final.csv 경로> <recipe_ingredient_cleaned.csv 경로>")
        return
    
    # 컬럼명 확인 및 출력
    print(f"\n📋 레시피 파일 컬럼: {list(df_recipes.columns)}")
    print(f"📋 재료 파일 컬럼: {list(df_ingredients.columns)}")
    
    # DB 연결
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 스키마 업데이트 (컬럼이 없으면 추가)
    try:
        cursor.execute("""
            ALTER TABLE recipe 
            ADD COLUMN IF NOT EXISTS main_ingredients TEXT COMMENT '주재료',
            ADD COLUMN IF NOT EXISTS sub_ingredients TEXT COMMENT '부재료'
        """)
        print("✅ 데이터베이스 스키마 업데이트 완료")
    except Exception as e:
        print(f"⚠️ 스키마 업데이트 (이미 존재할 수 있음): {e}")
    
    # 재료 데이터를 레시피 ID로 매핑
    ingredient_map = {}
    
    # 재료 파일 처리 (레시피 ID별로 재료 목록 구성)
    # 컬럼명에 따라 수정 필요
    recipe_id_col = None
    ingredient_col = None
    
    for col in df_ingredients.columns:
        col_lower = col.lower()
        if 'id' in col_lower or 'recipe' in col_lower:
            recipe_id_col = col
        elif 'ingredient' in col_lower or '재료' in col or 'name' in col_lower:
            ingredient_col = col
    
    if recipe_id_col and ingredient_col:
        print(f"\n🔗 재료 데이터 매핑 중...")
        for _, row in df_ingredients.iterrows():
            recipe_id = row[recipe_id_col]
            ingredient = row[ingredient_col]
            
            if pd.notna(ingredient):
                if recipe_id not in ingredient_map:
                    ingredient_map[recipe_id] = []
                ingredient_map[recipe_id].append(clean_ingredient(str(ingredient)))
        print(f"✅ {len(ingredient_map)}개 레시피의 재료 매핑 완료")
    else:
        print("⚠️ 재료 파일 컬럼 자동 감지 실패. 수동으로 컬럼명을 확인해주세요.")
        print(f"   재료 파일 컬럼: {list(df_ingredients.columns)}")
        return
    
    # 레시피 처리
    batch = []
    processed = 0
    
    recipe_id_col_recipes = None
    title_col = None
    
    for col in df_recipes.columns:
        col_lower = col.lower()
        if 'id' in col_lower or 'recipe' in col_lower:
            recipe_id_col_recipes = col
        elif 'title' in col_lower or '제목' in col or 'name' in col_lower:
            title_col = col
    
    for idx, row in df_recipes.iterrows():
        try:
            recipe_id = row[recipe_id_col_recipes] if recipe_id_col_recipes else idx + 1
            title = row[title_col] if title_col else ""
            
            # 해당 레시피의 재료 목록
            ingredients_list = ingredient_map.get(recipe_id, [])
            
            # 주재료/부재료 분류
            main_list = []
            sub_list = []
            
            for ing in ingredients_list:
                if ing:
                    is_main, cleaned = classify_main_sub(ing, str(title))
                    if cleaned:
                        if is_main:
                            main_list.append(cleaned)
                        else:
                            sub_list.append(cleaned)
            
            main_ingredients = ",".join(main_list) if main_list else ""
            sub_ingredients = ",".join(sub_list) if sub_list else ""
            
            # 기존 ingredients 컬럼도 유지 (하위 호환성)
            all_ingredients = ",".join(ingredients_list) if ingredients_list else ""
            
            batch.append((main_ingredients, sub_ingredients, recipe_id))
            
            if len(batch) >= batch_size:
                # UPDATE 쿼리 실행
                cursor.executemany(
                    """UPDATE recipe 
                       SET main_ingredients = %s, sub_ingredients = %s 
                       WHERE id = %s""",
                    batch
                )
                conn.commit()
                processed += len(batch)
                print(f"✅ {processed}개 레시피 업데이트 완료")
                batch.clear()
                
        except Exception as e:
            print(f"❌ 레시피 {recipe_id} 처리 중 오류: {e}")
            continue
    
    # 남은 배치 처리
    if batch:
        cursor.executemany(
            """UPDATE recipe 
               SET main_ingredients = %s, sub_ingredients = %s 
               WHERE id = %s""",
            batch
        )
        conn.commit()
        processed += len(batch)
        print(f"✅ 마지막 {len(batch)}개 레시피 업데이트 완료")
    
    cursor.close()
    conn.close()
    print(f"\n🎉 전체 처리 완료! 총 {processed}개 레시피 업데이트됨")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("📝 사용법:")
        print("   python load_csv_with_main_sub.py <recipe_final.csv> <recipe_ingredient_cleaned.csv>")
        print("\n📌 예시:")
        print("   python load_csv_with_main_sub.py ~/Downloads/data/recipe_final.csv ~/Downloads/data/recipe_ingredient_cleaned.csv")
        sys.exit(1)
    
    recipe_file = sys.argv[1]
    ingredient_file = sys.argv[2]
    
    if not os.path.exists(recipe_file):
        print(f"❌ 레시피 파일을 찾을 수 없습니다: {recipe_file}")
        sys.exit(1)
    
    if not os.path.exists(ingredient_file):
        print(f"❌ 재료 파일을 찾을 수 없습니다: {ingredient_file}")
        sys.exit(1)
    
    load_and_process_csv(recipe_file, ingredient_file)

