"""users 테이블 복구 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

def restore_users_table():
    """가장 최근 백업 테이블에서 users 테이블 복구"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("users 테이블 복구")
        print("="*60)
        
        # 1. 백업 테이블 목록 확인
        print("\n[1단계] 백업 테이블 확인...")
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'users_backup%' 
            ORDER BY name DESC
        """))
        backup_tables = [row[0] for row in result]
        
        if not backup_tables:
            print("  백업 테이블을 찾을 수 없습니다!")
            return
        
        print(f"  발견된 백업 테이블: {len(backup_tables)}개")
        for i, table in enumerate(backup_tables[:5], 1):  # 최대 5개만 표시
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"    {i}. {table}: {count}개 행")
        
        # 가장 최근 백업 사용
        latest_backup = backup_tables[0]
        print(f"\n  사용할 백업: {latest_backup}")
        
        result = db.execute(text(f"SELECT COUNT(*) FROM {latest_backup}"))
        backup_count = result.scalar()
        print(f"  백업 데이터: {backup_count}개 행")
        
        if backup_count == 0:
            print("\n  경고: 백업 테이블이 비어있습니다!")
            # 다른 백업 테이블 확인
            for table in backup_tables[1:]:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                if count > 0:
                    print(f"  대안 백업 발견: {table} ({count}개 행)")
                    latest_backup = table
                    backup_count = count
                    break
        
        # 2. VIEW 삭제
        print("\n[2단계] VIEW 삭제...")
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
        
        # 3. 현재 users 테이블 확인
        print("\n[3단계] 현재 users 테이블 확인...")
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        current_count = result.scalar()
        print(f"  현재 users 테이블: {current_count}개 행")
        
        # 4. 백업 테이블 구조 확인
        print("\n[4단계] 백업 테이블 구조 확인...")
        result = db.execute(text(f"PRAGMA table_info({latest_backup})"))
        columns = [row[1] for row in result]
        print(f"  백업 테이블 컬럼: {', '.join(columns)}")
        
        # 5. users 테이블 삭제 및 재생성
        print("\n[5단계] users 테이블 재생성...")
        db.execute(text("DROP TABLE IF EXISTS users"))
        
        # 백업 테이블 구조에 맞춰 users 테이블 생성
        # headquarters 컬럼이 있는지 확인
        has_headquarters = 'headquarters' in columns
        
        if has_headquarters:
            # headquarters 포함 버전
            db.execute(text(f"""
                CREATE TABLE users AS
                SELECT * FROM {latest_backup}
            """))
        else:
            # headquarters 없는 버전
            db.execute(text(f"""
                CREATE TABLE users AS
                SELECT * FROM {latest_backup}
            """))
        
        db.commit()
        print("  재생성 완료")
        
        # 6. 인덱스 재생성
        print("\n[6단계] 인덱스 재생성...")
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        db.commit()
        print("  인덱스 재생성 완료")
        
        # 7. 복구 확인
        print("\n[7단계] 복구 확인...")
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        restored_count = result.scalar()
        print(f"  복구된 데이터: {restored_count}개 행")
        
        if restored_count == backup_count:
            print("  복구 성공!")
        else:
            print(f"  경고: 복구된 행 수({restored_count})가 백업 행 수({backup_count})와 다릅니다!")
        
        print("\n" + "="*60)
        print("users 테이블 복구 완료!")
        print("="*60)
        print(f"\n백업 테이블: {latest_backup}")
        print(f"복구된 행 수: {restored_count}개")
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
    restore_users_table()

