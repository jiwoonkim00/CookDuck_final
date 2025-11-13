"""
CSV 파일에서 데이터를 읽어서 새로운 recipe_new 테이블에 저장하는 스크립트
recipe_final.csv와 recipe_ingredient_cleaned.csv를 사용
주재료/부재료는 recipe_ingredient_cleaned.csv의 재료타입명에서 자동으로 구분
"""

import pandas as pd
import pymysql
import os
import sys
from typing import Dict, List, Tuple
import re
from tqdm import tqdm

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
    """재료명 정제"""
    if pd.isna(ingredient) or not ingredient:
        return ""
    return str(ingredient).strip()

def load_and_process_csv(
    recipe_file: str = "recipe_final.csv",
    ingredient_file: str = "recipe_ingredient_cleaned.csv",
    batch_size: int = 1000
) -> None:
    """
    CSV 파일을 읽어서 recipe_new 테이블에 저장
    """
    print("=" * 60)
    print("📖 CSV 파일 로딩 시작")
    print("=" * 60)
    
    # CSV 파일 읽기
    try:
        print(f"\n📂 레시피 파일 읽기: {recipe_file}")
        df_recipes = pd.read_csv(recipe_file, encoding='utf-8')
        print(f"✅ 레시피 데이터: {len(df_recipes)}개 행")
        print(f"📋 컬럼: {list(df_recipes.columns)}")
    except Exception as e:
        print(f"❌ 레시피 파일 읽기 실패: {e}")
        return
    
    # 재료 파일 읽기
    df_ingredients = None
    ingredient_map = {}  # {recipe_id: {main: [...], sub: [...]}}
    
    if ingredient_file and os.path.exists(ingredient_file):
        try:
            print(f"\n📂 재료 파일 읽기: {ingredient_file}")
            df_ingredients = pd.read_csv(ingredient_file, encoding='utf-8')
            print(f"✅ 재료 데이터: {len(df_ingredients)}개 행")
            print(f"📋 컬럼: {list(df_ingredients.columns)}")
            
            # 재료 데이터를 레시피 ID로 매핑 (주재료/부재료 구분)
            print(f"\n🔗 재료 데이터 매핑 중 (주재료/부재료 구분)...")
            for _, row in tqdm(df_ingredients.iterrows(), total=len(df_ingredients), desc="재료 매핑"):
                recipe_id = row['레시피 코드'] if '레시피 코드' in row else row.get('recipe_id', None)
                ingredient = row['재료명'] if '재료명' in row else row.get('ingredient_name', None)
                ingredient_type = row['재료타입명'] if '재료타입명' in row else row.get('ingredient_type', None)
                
                if pd.isna(recipe_id) or pd.isna(ingredient):
                    continue
                
                recipe_id = int(recipe_id)
                ingredient = clean_ingredient(str(ingredient))
                
                if recipe_id not in ingredient_map:
                    ingredient_map[recipe_id] = {'main': [], 'sub': [], 'all': []}
                
                ingredient_map[recipe_id]['all'].append(ingredient)
                
                # 재료타입명으로 주재료/부재료 구분
                if ingredient_type and '주재료' in str(ingredient_type):
                    ingredient_map[recipe_id]['main'].append(ingredient)
                elif ingredient_type and ('부재료' in str(ingredient_type) or '조미료' in str(ingredient_type)):
                    ingredient_map[recipe_id]['sub'].append(ingredient)
                else:
                    # 재료타입명이 없으면 기본적으로 주재료로 간주
                    ingredient_map[recipe_id]['main'].append(ingredient)
            
            print(f"✅ {len(ingredient_map)}개 레시피의 재료 매핑 완료")
        except Exception as e:
            print(f"⚠️ 재료 파일 읽기 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # DB 연결
    print(f"\n🔌 데이터베이스 연결 중...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("\n💡 Docker 컨테이너가 실행 중인지 확인하세요:")
        print("   docker-compose ps")
        return
    
    # 테이블 생성 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM recipe_new")
        count = cursor.fetchone()[0]
        print(f"📊 기존 recipe_new 테이블에 {count}개 레시피 존재")
        
        # 사용자 확인
        if count > 0:
            response = input(f"\n⚠️  기존 데이터가 있습니다. 덮어쓰시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("❌ 작업 취소됨")
                cursor.close()
                conn.close()
                return
            
            # 기존 데이터 삭제
            cursor.execute("TRUNCATE TABLE recipe_new")
            conn.commit()
            print("🗑️  기존 데이터 삭제 완료")
    except Exception as e:
        print(f"⚠️  테이블 확인 실패: {e}")
        print("💡 테이블을 생성하세요: docker-compose exec mariadb mysql -uroot -proot recipe_db < create_recipe_new_table.sql")
    
    # 레시피 컬럼명 매핑
    recipe_id_col = '레시피 코드' if '레시피 코드' in df_recipes.columns else 'recipe_id'
    title_col = '레시피 이름' if '레시피 이름' in df_recipes.columns else 'recipe_name'
    content_col = '요리설명' if '요리설명' in df_recipes.columns else 'content'
    
    print(f"\n📝 컬럼 매핑:")
    print(f"   ID: {recipe_id_col}")
    print(f"   제목: {title_col}")
    print(f"   내용: {content_col}")
    
    # 레시피 처리 및 삽입
    print(f"\n💾 데이터 삽입 시작...")
    batch = []
    processed = 0
    errors = 0
    
    for idx, row in tqdm(df_recipes.iterrows(), total=len(df_recipes), desc="레시피 삽입"):
        try:
            # 레시피 기본 정보 추출
            recipe_id = int(row[recipe_id_col]) if pd.notna(row[recipe_id_col]) else None
            title = str(row[title_col]) if pd.notna(row[title_col]) else ""
            content = str(row[content_col]) if pd.notna(row[content_col]) else ""
            
            if not title:
                errors += 1
                continue
            
            # 재료 정보 가져오기
            main_ingredients = []
            sub_ingredients = []
            all_ingredients = []
            
            if recipe_id and recipe_id in ingredient_map:
                # 재료 파일에서 주재료/부재료 정보 사용
                main_ingredients = ingredient_map[recipe_id]['main']
                sub_ingredients = ingredient_map[recipe_id]['sub']
                all_ingredients = ingredient_map[recipe_id]['all']
            elif '재료명' in df_recipes.columns:
                # 재료명 컬럼이 있으면 직접 사용 (쉼표로 구분)
                ing_str = str(row['재료명']) if pd.notna(row['재료명']) else ""
                if ing_str:
                    all_ingredients = [clean_ingredient(i) for i in ing_str.split(',') if clean_ingredient(i)]
                    # 간단한 분류 (주재료로 모두 처리)
                    main_ingredients = all_ingredients
                    sub_ingredients = []
            
            # 재료 문자열 변환
            all_ingredients_str = ",".join(all_ingredients) if all_ingredients else ""
            main_ingredients_str = ",".join(main_ingredients) if main_ingredients else ""
            sub_ingredients_str = ",".join(sub_ingredients) if sub_ingredients else ""
            
            # 배치에 추가
            batch.append((
                title,
                all_ingredients_str,
                main_ingredients_str,
                sub_ingredients_str,
                "",  # tools (없음)
                content
            ))
            
            # 배치 크기만큼 모이면 삽입
            if len(batch) >= batch_size:
                cursor.executemany(
                    """INSERT INTO recipe_new 
                       (title, ingredients, main_ingredients, sub_ingredients, tools, content) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    batch
                )
                conn.commit()
                processed += len(batch)
                print(f"✅ {processed}개 레시피 삽입 완료")
                batch.clear()
                
        except Exception as e:
            errors += 1
            if errors <= 5:  # 처음 5개 에러만 출력
                print(f"❌ 레시피 {idx} 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()
            continue
    
    # 남은 배치 처리
    if batch:
        cursor.executemany(
            """INSERT INTO recipe_new 
               (title, ingredients, main_ingredients, sub_ingredients, tools, content) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            batch
        )
        conn.commit()
        processed += len(batch)
        print(f"✅ 마지막 {len(batch)}개 레시피 삽입 완료")
    
    # 최종 통계
    cursor.execute("SELECT COUNT(*) FROM recipe_new")
    final_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN main_ingredients IS NOT NULL AND main_ingredients != '' THEN 1 ELSE 0 END) as with_main,
            SUM(CASE WHEN sub_ingredients IS NOT NULL AND sub_ingredients != '' THEN 1 ELSE 0 END) as with_sub
        FROM recipe_new
    """)
    stats = cursor.fetchone()
    
    print("\n" + "=" * 60)
    print("🎉 데이터 로딩 완료!")
    print("=" * 60)
    print(f"✅ 총 {final_count}개 레시피 저장됨")
    print(f"📊 주재료 정보: {stats[1]}개 레시피")
    print(f"📊 부재료 정보: {stats[2]}개 레시피")
    print(f"⚠️  에러 발생: {errors}개")
    
    cursor.close()
    conn.close()
    print("\n✅ 작업 완료!")

if __name__ == "__main__":
    # 현재 디렉토리의 CSV 파일 사용
    recipe_file = "recipe_final.csv"
    ingredient_file = "recipe_ingredient_cleaned.csv"
    
    # 명령줄 인자로 경로 지정 가능
    if len(sys.argv) > 1:
        recipe_file = sys.argv[1]
    if len(sys.argv) > 2:
        ingredient_file = sys.argv[2]
    
    if not os.path.exists(recipe_file):
        print(f"❌ 레시피 파일을 찾을 수 없습니다: {recipe_file}")
        print(f"💡 현재 디렉토리: {os.getcwd()}")
        sys.exit(1)
    
    if not os.path.exists(ingredient_file):
        print(f"⚠️  재료 파일을 찾을 수 없습니다 (무시하고 진행): {ingredient_file}")
        ingredient_file = None
    
    load_and_process_csv(recipe_file, ingredient_file)
