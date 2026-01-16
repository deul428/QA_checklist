"""
User 테이블에 조직 정보 컬럼을 추가하는 마이그레이션 스크립트

사용법:
    python backend/dummy/add_user_columns.py
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import engine

def add_user_columns():
    """User 테이블에 조직 정보 컬럼 추가"""
    with engine.connect() as conn:
        try:
            # SQLite는 ALTER TABLE ADD COLUMN을 지원하지만, 컬럼이 이미 존재하는지 확인 필요
            # 각 컬럼을 추가 (이미 존재하면 에러 무시)
            columns_to_add = [
                ("division", "VARCHAR(100)"),
                ("general_headquarters", "VARCHAR(100)"),
                ("headquarters", "VARCHAR(100)"),
                ("department", "VARCHAR(100)"),
                ("position", "VARCHAR(50)"),
                ("role", "VARCHAR(50)"),
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    # 컬럼이 이미 존재하는지 확인
                    result = conn.execute(text(f"PRAGMA table_info(users)"))
                    existing_columns = [row[1] for row in result]
                    
                    if column_name not in existing_columns:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                        conn.commit()
                        print(f"  [추가] {column_name} 컬럼이 추가되었습니다.")
                    else:
                        print(f"  [건너뜀] {column_name} 컬럼이 이미 존재합니다.")
                except Exception as e:
                    print(f"  [오류] {column_name} 컬럼 추가 중 오류: {e}")
                    conn.rollback()
            
            print("\n" + "="*50)
            print("마이그레이션 완료!")
            print("="*50)
            
        except Exception as e:
            print(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    add_user_columns()

