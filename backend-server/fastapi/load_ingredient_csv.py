"""
recipe_ingredient_cleaned.csv 내용을 MariaDB recipe_ingredient_cleaned 테이블에 적재하는 스크립트
"""

import os
import sys
import pandas as pd
import pymysql
from tqdm import tqdm

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "root",
    "db": "recipe_db",
    "charset": "utf8mb4",
}


def load_csv(filepath: str = "recipe_ingredient_cleaned.csv", batch_size: int = 1000) -> None:
    print("=" * 60)
    print(f"📖 {filepath} 적재 시작")
    print("=" * 60)

    if not os.path.exists(filepath):
        print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
        print(f"💡 현재 디렉토리: {os.getcwd()}")
        sys.exit(1)

    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except Exception as exc:
        print(f"❌ CSV 로드 실패: {exc}")
        sys.exit(1)

    print(f"✅ 총 {len(df)}행 로드")
    print(f"📋 컬럼: {list(df.columns)}")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE recipe_ingredient_cleaned")
    conn.commit()
    print("🧹 기존 데이터 초기화 완료")

    insert_sql = """
        INSERT INTO recipe_ingredient_cleaned (
            recipe_code,
            ingredient_order,
            ingredient_name,
            ingredient_amount,
            ingredient_type_code,
            ingredient_type_name
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """

    batch = []
    processed = 0
    for _, row in tqdm(df.iterrows(), total=len(df), desc="행 삽입"):
        recipe_code = row.get("레시피 코드")
        ingredient_order = row.get("재료순번")
        ingredient_name = row.get("재료명")
        ingredient_amount = row.get("재료용량")
        ingredient_type_code = row.get("재료타입 코드")
        ingredient_type_name = row.get("재료타입명")

        batch.append(
            (
                int(recipe_code) if not pd.isna(recipe_code) else None,
                int(ingredient_order) if not pd.isna(ingredient_order) else None,
                str(ingredient_name).strip() if not pd.isna(ingredient_name) else "",
                str(ingredient_amount).strip() if not pd.isna(ingredient_amount) else "",
                str(ingredient_type_code).strip() if not pd.isna(ingredient_type_code) else "",
                str(ingredient_type_name).strip() if not pd.isna(ingredient_type_name) else "",
            )
        )

        if len(batch) >= batch_size:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            processed += len(batch)
            print(f"✅ {processed}행 삽입 완료")
            batch.clear()

    if batch:
        cursor.executemany(insert_sql, batch)
        conn.commit()
        processed += len(batch)

    print(f"🎉 총 {processed}행 삽입 완료")

    cursor.close()
    conn.close()
    print("✅ 작업 완료")


if __name__ == "__main__":
    target_file = "recipe_ingredient_cleaned.csv"
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    load_csv(target_file)

