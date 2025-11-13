from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 환경에 따라 데이터베이스 URL 설정
# Docker 컨테이너 내부에서는 mariadb 서비스명 사용
DB_URL = f"mysql+pymysql://root:root@mariadb:3306/recipe_db"



engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)