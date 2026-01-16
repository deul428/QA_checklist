"""
user_system_assignments 테이블 ID 초기화 및 데이터 재import 스크립트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

def reset_table_and_id():
    """테이블을 완전히 삭제하고 ID를 1부터 시작하도록 재생성"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("user_system_assignments 테이블 초기화")
        print("="*60)
        
        # 1. 테이블 삭제
        print("\n[1단계] 기존 테이블 삭제...")
        db.execute(text("DROP TABLE IF EXISTS user_system_assignments"))
        db.commit()
        print("  삭제 완료")
        
        # 2. 새 테이블 생성
        print("\n[2단계] 새 테이블 생성 (ID 1부터 시작)...")
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
        
        # 3. 인덱스 생성
        print("\n[3단계] 인덱스 생성...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_user_id ON user_system_assignments(user_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_system_id ON user_system_assignments(system_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_user_name ON user_system_assignments(user_name)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_usa_item_name ON user_system_assignments(item_name)"))
        db.commit()
        print("  인덱스 생성 완료")
        
        # 4. SQLite의 AUTOINCREMENT 시퀀스 초기화
        print("\n[4단계] ID 시퀀스 초기화...")
        db.execute(text("DELETE FROM sqlite_sequence WHERE name='user_system_assignments'"))
        db.commit()
        print("  초기화 완료")
        
        print("\n" + "="*60)
        print("테이블 초기화 완료! ID는 1부터 시작합니다.")
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
    reset_table_and_id()

