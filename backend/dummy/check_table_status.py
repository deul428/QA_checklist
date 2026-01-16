"""테이블 상태 확인"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'users%'"))
    print("Users 관련 테이블:")
    for row in result:
        print(f"  {row[0]}")
    
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    if result.fetchone():
        result = db.execute(text("PRAGMA table_info(users)"))
        print("\nusers 테이블 컬럼:")
        for row in result:
            print(f"  {row[1]} ({row[2]})")
finally:
    db.close()

