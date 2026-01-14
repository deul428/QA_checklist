from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# SQLite를 기본값으로 사용 (개발 환경)
# PostgreSQL을 사용하려면 .env 파일에 DATABASE_URL을 설정하세요
# database 폴더는 backend와 같은 레벨에 있음
if not os.getenv("DATABASE_URL"):
    # backend/src/services/database.py에서 backend 폴더로 이동 후 database 폴더로
    backend_dir = Path(__file__).parent.parent.parent
    db_path = backend_dir.parent / "database" / "qa_checklist.db"
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

# SQLite는 check_same_thread=False 필요
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

