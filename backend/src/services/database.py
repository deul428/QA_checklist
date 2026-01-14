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
# 프로젝트 루트 계산: backend/src/services/database.py -> backend -> 프로젝트 루트
project_root = Path(__file__).parent.parent.parent.parent

if not os.getenv("DATABASE_URL"):
    # DATABASE_URL이 .env에 없으면 자동으로 프로젝트 루트 기준으로 생성
    db_path = project_root / "database" / "qa_checklist.db"
    # 절대 경로를 문자열로 변환하고 Windows 경로 구분자를 처리
    db_path_str = str(db_path.absolute()).replace("\\", "/")
    DATABASE_URL = f"sqlite:///{db_path_str}"
else:
    # .env에 DATABASE_URL이 있으면 사용하되, 상대 경로인 경우 프로젝트 루트 기준으로 해석
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("sqlite:///"):
        path_part = db_url.replace("sqlite:///", "")
        path_obj = Path(path_part)
        
        if not path_obj.is_absolute():
            # 상대 경로인 경우 (예: sqlite:///../database/qa_checklist.db)
            # ../database/qa_checklist.db를 프로젝트 루트 기준으로 해석
            # ../는 프로젝트 루트의 부모가 아니라, backend 폴더 기준이므로
            # 프로젝트 루트에서 직접 database/qa_checklist.db로 해석
            if path_part.startswith("../"):
                # ../를 제거하고 프로젝트 루트 기준으로 해석
                clean_path = path_part.replace("../", "", 1)
                db_path = (project_root / clean_path).resolve()
            else:
                # 상대 경로가 ../로 시작하지 않으면 프로젝트 루트 기준
                db_path = (project_root / path_part).resolve()
            
            db_path_str = str(db_path.absolute()).replace("\\", "/")
            DATABASE_URL = f"sqlite:///{db_path_str}"
        else:
            # 절대 경로인 경우 그대로 사용
            DATABASE_URL = db_url
    else:
        # PostgreSQL 등 다른 DB인 경우 그대로 사용
        DATABASE_URL = db_url

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

