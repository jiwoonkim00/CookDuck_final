# 파일 이름: db_test_columns.py
# 실행 위치: /Users/server/Desktop/cookDuck_backup/backend-server/fastapi/
# 역할: 'recipe_ingredient_cleaned' 테이블의 "실제" 컬럼명(Field)을 확인합니다.

import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, InterfaceError

# --- [1. DB 연결 정보 설정] ---
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "recipe_db"
DB_HOST = "127.0.0.1" 
DB_PORT = "3307" # <-- 'db_test.py'에서 성공한 3307 포트
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"--- DB 접속 테스트 시작 ---")
print(f"접속 대상: {DB_HOST}:{DB_PORT}, 데이터베이스: {DB_NAME}")

try:
    # --- [2. DB 접속] ---
    engine = create_engine(DB_URL)
    
    with engine.connect() as connection:
        print("\n✅ [성공] DB 연결 성공!")

        # --- [3. (★핵심★) 'recipe_ingredient_cleaned' 테이블 컬럼명 확인] ---
        print("\n--- 'recipe_ingredient_cleaned' 테이블의 실제 컬럼명 ---")
        
        # MySQL/MariaDB에서 테이블 구조를 보는 명령어
        query = text("DESCRIBE recipe_ingredient_cleaned;") 
        
        result = connection.execute(query)
        
        if result.rowcount == 0:
            print("🚨 [오류] 'recipe_ingredient_cleaned' 테이블을 찾을 수 없습니다.")
        else:
            # (Pandas로 깔끔하게 출력)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            print(df.to_string())
            
            print("\n--- [분석] ---")
            print("위 'Field' 열에 있는 '영어' 컬럼명 (예: recipe_id, ingredient_name, ingredient_type)을")
            print("'run_rag_standalone_test.py'의 '로직 4' SQL 쿼리에 반영해야 합니다.")

        print("\n✅ [최종 성공] DB 스키마(구조) 테스트가 완료되었습니다.")

except (OperationalError, InterfaceError) as e:
    print(f"\n🚨 [오류] DB 연결 실패!")
    print(f"에러 메시지: {e}")
except Exception as e:
    print(f"\n🚨 [알 수 없는 오류] {e}")