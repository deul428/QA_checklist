"""데이터베이스 ID 확인 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

def check_ids():
    """user_system_assignments 테이블의 ID 확인"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("user_system_assignments 테이블 ID 확인")
        print("="*60)
        
        # 전체 행 수
        result = db.execute(text("SELECT COUNT(*) FROM user_system_assignments"))
        total_count = result.scalar()
        print(f"\n총 행 수: {total_count}개")
        
        # 최소/최대 ID
        result = db.execute(text("SELECT MIN(id), MAX(id) FROM user_system_assignments"))
        min_id, max_id = result.fetchone()
        print(f"최소 ID: {min_id}")
        print(f"최대 ID: {max_id}")
        
        # 처음 5개와 마지막 5개 확인
        print("\n처음 5개:")
        result = db.execute(text("""
            SELECT id, user_name, system_id, item_name 
            FROM user_system_assignments 
            ORDER BY id 
            LIMIT 5
        """))
        for row in result:
            print(f"  ID {row[0]}: {row[1]} -> system_id={row[2]}, item={row[3][:30]}...")
        
        print("\n마지막 5개:")
        result = db.execute(text("""
            SELECT id, user_name, system_id, item_name 
            FROM user_system_assignments 
            ORDER BY id DESC 
            LIMIT 5
        """))
        for row in result:
            print(f"  ID {row[0]}: {row[1]} -> system_id={row[2]}, item={row[3][:30]}...")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_ids()

