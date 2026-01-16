"""checklist_records_logs 테이블 생성 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal, engine, Base
from models.models import ChecklistRecordLog

def create_logs_table():
    """checklist_records_logs 테이블 생성"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("checklist_records_logs 테이블 생성")
        print("="*60)
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine, tables=[ChecklistRecordLog.__table__])
        print("\n테이블 생성 완료!")
        
        # 기존 checklist_records 데이터를 로그로 마이그레이션
        print("\n기존 checklist_records 데이터를 로그로 마이그레이션...")
        result = db.execute(text("""
            INSERT INTO checklist_records_logs 
            (user_id, check_item_id, check_date, status, notes, action, created_at)
            SELECT 
                user_id,
                check_item_id,
                check_date,
                status,
                notes,
                'CREATE' as action,
                checked_at as created_at
            FROM checklist_records
        """))
        db.commit()
        print(f"마이그레이션 완료: {result.rowcount}개 레코드")
        
        print("\n" + "="*60)
        print("완료!")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_logs_table()

