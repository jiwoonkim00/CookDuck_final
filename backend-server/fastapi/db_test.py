# 파일 이름: db_test.py
# 실행 위치: /Users/server/Desktop/cookDuck_backup/backend-server/fastapi/
# 역할: (수정본) 3307 포트로 DB에 직접 접속하여 'recipe_new' 테이블을 확인합니다.

import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, InterfaceError

# --- [1. (★핵심 수정★) DB 연결 정보 설정] ---
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "recipe_db"
DB_HOST = "127.0.0.1" 
DB_PORT = "3307" # <-- docker ps에서 확인된 '3307' 포트로 수정

# SQLAlchemy 연결 문자열 생성
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"--- DB 접속 테스트 시작 ---")
print(f"접속 대상: {DB_HOST}:{DB_PORT}, 데이터베이스: {DB_NAME}")

try:
    # --- [2. DB 접속] ---
    engine = create_engine(DB_URL)
    
    with engine.connect() as connection:
        print("\n✅ [성공] DB 연결 성공!")

        # --- [3. Table 확인] ---
        print("\n--- 1. 'recipe_db'의 모든 테이블 목록 ---")
        tables_query = text("SHOW TABLES;")
        tables_result = connection.execute(tables_query)
        tables_df = pd.DataFrame(tables_result.fetchall(), columns=tables_result.keys())
        print(tables_df.to_string())

        # --- [4. 'recipe_new' 테이블 5개 행 출력] ---
        print("\n--- 2. 'recipe_new' 테이블 상위 5개 행 ---")
        recipe_query = text("SELECT * FROM recipe_new LIMIT 5;")
        recipe_result = connection.execute(recipe_query)
        
        if recipe_result.rowcount == 0:
            print("🚨 [경고] 'recipe_new' 테이블은 존재하지만, 데이터가 비어있습니다.")
        else:
            recipe_df = pd.DataFrame(recipe_result.fetchall(), columns=recipe_result.keys())
            print(recipe_df.to_string())

        print("\n✅ [최종 성공] DB 테스트가 완료되었습니다.")

except ImportError:
    print("\n🚨 [오류] 'pymysql' 또는 'sqlalchemy' 라이브러리가 없습니다.")
    print(" (venv_vision_311) ... % pip install sqlalchemy pymysql pandas")
except (OperationalError, InterfaceError) as e:
    print(f"\n🚨 [오류] DB 연결 실패!")
    print(f"에러 메시지: {e}")
    print("\n--- [해결책] ---")
    print("1. 'cookduck-mariadb' Docker 컨테이너가 'Up' 상태인지 확인하세요. (docker ps)")
    print(f"2. DB가 Mac mini의 {DB_HOST}:{DB_PORT} 포트로 정확히 포워딩되었는지 확인하세요.")
except Exception as e:
    print(f"\n🚨 [알 수 없는 오류] {e}")