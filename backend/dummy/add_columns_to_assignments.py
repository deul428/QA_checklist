"""
user_system_assignments 테이블에 user_name과 item_name 컬럼 추가 스크립트

기존 구조:
- user_id, system_id

새 구조:
- user_id, user_name, system_id, item_name

주의: item_name은 여러 개일 수 있으므로, 각 항목마다 별도 행으로 저장됩니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal, engine

def add_columns():
    """user_system_assignments 테이블에 user_name과 item_name 컬럼 추가"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("user_system_assignments 테이블 구조 변경 시작")
        print("="*60)
        
        # 1. 기존 데이터 백업 (새 테이블로)
        print("\n[1단계] 기존 데이터 백업...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_system_assignments_backup AS
            SELECT * FROM user_system_assignments
        """))
        db.commit()
        print("  백업 완료")
        
        # 2. 기존 테이블 삭제
        print("\n[2단계] 기존 테이블 삭제...")
        db.execute(text("DROP TABLE IF EXISTS user_system_assignments"))
        db.commit()
        print("  삭제 완료")
        
        # 3. 새 테이블 생성 (user_name, item_name 포함)
        print("\n[3단계] 새 테이블 생성...")
        db.execute(text("""
            CREATE TABLE user_system_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name VARCHAR(100) NOT NULL,
                system_id INTEGER NOT NULL,
                item_name VARCHAR(200) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE CASCADE
            )
        """))
        db.commit()
        print("  생성 완료")
        
        # 4. 인덱스 생성
        print("\n[4단계] 인덱스 생성...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_user_id ON user_system_assignments(user_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_system_id ON user_system_assignments(system_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_user_name ON user_system_assignments(user_name)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_item_name ON user_system_assignments(item_name)"))
        db.commit()
        print("  인덱스 생성 완료")
        
        print("\n" + "="*60)
        print("테이블 구조 변경 완료!")
        print("="*60)
        print("\n다음 단계: import_checklist_data.py를 실행하여 데이터를 다시 import하세요.")
        print("  python backend/dummy/import_checklist_data.py database/checklist_data_0115_bom.csv")
        
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    add_columns()

