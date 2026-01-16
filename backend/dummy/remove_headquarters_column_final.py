"""
headquarters 컬럼 삭제 스크립트 (최종)

headquarters와 department가 일치하므로 headquarters 컬럼을 삭제합니다.
SQLite는 컬럼 삭제를 직접 지원하지 않으므로 테이블 재생성이 필요합니다.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

def remove_headquarters_column():
    """users 테이블에서 headquarters 컬럼 삭제"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("headquarters 컬럼 삭제")
        print("="*60)
        
        # 1. VIEW 삭제 (users 테이블을 참조하는 VIEW들)
        print("\n[1단계] VIEW 삭제...")
        views_to_drop = [
            "checklist_records_view",
            "user_system_assignments_view",
            "check_items_view",
            "user_system_assignments_with_items_view"
        ]
        for view_name in views_to_drop:
            try:
                db.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
                print(f"  {view_name} 삭제 완료")
            except Exception as e:
                print(f"  {view_name} 삭제 실패 (없을 수 있음): {e}")
        db.commit()
        
        # 2. 백업 테이블 생성
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"users_backup_before_remove_hq_{timestamp}"
        
        print(f"\n[2단계] 백업 테이블 생성: {backup_table}")
        db.execute(text(f"""
            CREATE TABLE {backup_table} AS
            SELECT * FROM users
        """))
        db.commit()
        
        result = db.execute(text(f"SELECT COUNT(*) FROM {backup_table}"))
        backup_count = result.scalar()
        print(f"  백업 완료: {backup_count}개 행")
        
        # 3. 기존 users_new 테이블 삭제 (있다면)
        print("\n[3단계] 기존 users_new 테이블 정리...")
        try:
            db.execute(text("DROP TABLE IF EXISTS users_new"))
            db.commit()
            print("  정리 완료")
        except Exception as e:
            print(f"  정리 실패 (없을 수 있음): {e}")
        
        # 4. 새 users 테이블 생성 (headquarters 제외)
        print("\n[4단계] 새 users 테이블 생성 (headquarters 제외)...")
        db.execute(text("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                division VARCHAR(100),
                general_headquarters VARCHAR(100),
                department VARCHAR(100),
                position VARCHAR(50),
                role VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        print("  생성 완료")
        
        # 5. 데이터 복사 (headquarters 제외)
        print("\n[5단계] 데이터 복사...")
        db.execute(text("""
            INSERT INTO users_new (
                id, employee_id, name, email, password_hash,
                division, general_headquarters, department,
                position, role, created_at, updated_at
            )
            SELECT 
                id, employee_id, name, email, password_hash,
                division, general_headquarters, department,
                position, role, created_at, updated_at
            FROM users
        """))
        db.commit()
        
        result = db.execute(text("SELECT COUNT(*) FROM users_new"))
        new_count = result.scalar()
        print(f"  복사 완료: {new_count}개 행")
        
        # 6. 기존 테이블 삭제 및 새 테이블로 교체
        print("\n[6단계] 테이블 교체...")
        db.execute(text("DROP TABLE users"))
        db.execute(text("ALTER TABLE users_new RENAME TO users"))
        db.commit()
        print("  교체 완료")
        
        # 7. 인덱스 재생성
        print("\n[7단계] 인덱스 재생성...")
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        db.commit()
        print("  인덱스 재생성 완료")
        
        print("\n" + "="*60)
        print("headquarters 컬럼 삭제 완료!")
        print("="*60)
        print(f"\n백업 테이블: {backup_table}")
        print("\n다음 단계: VIEW를 재생성하려면 다음 명령을 실행하세요:")
        print("  python backend/dummy/create_views.py")
        
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    remove_headquarters_column()

