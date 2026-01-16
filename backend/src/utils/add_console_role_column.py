"""
users 테이블에 console_role 컬럼 추가 및 기존 관리자 사번 업데이트 스크립트

사용법:
    python backend/src/utils/add_console_role_column.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal, engine

# 기존 관리자 사번 목록
ADMIN_EMPLOYEE_IDS = ["224147", "224005", "225016"]


def add_console_role_column():
    """console_role 컬럼 추가 및 기존 관리자 권한 부여"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("console_role 컬럼 추가 및 관리자 권한 설정")
        print("=" * 60)
        
        # 1. 컬럼 존재 여부 확인
        print("\n[1단계] console_role 컬럼 존재 여부 확인")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM pragma_table_info('users') WHERE name='console_role'
            """))
            column_exists = result.fetchone() is not None
        
        if column_exists:
            print("  console_role 컬럼이 이미 존재합니다.")
        else:
            print("  console_role 컬럼을 추가합니다...")
            with engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE users ADD COLUMN console_role BOOLEAN DEFAULT 0 NOT NULL
                """))
                conn.commit()
            print("  console_role 컬럼 추가 완료")
        
        # 2. 기존 관리자 사번에 권한 부여
        print("\n[2단계] 기존 관리자 사번에 console_role 권한 부여")
        print(f"  관리자 사번: {', '.join(ADMIN_EMPLOYEE_IDS)}")
        
        updated_count = 0
        for employee_id in ADMIN_EMPLOYEE_IDS:
            result = db.execute(text("""
                UPDATE users 
                SET console_role = 1 
                WHERE employee_id = :employee_id
            """), {"employee_id": employee_id})
            
            if result.rowcount > 0:
                updated_count += result.rowcount
                # 사용자 이름 확인
                user_result = db.execute(text("""
                    SELECT name FROM users WHERE employee_id = :employee_id
                """), {"employee_id": employee_id})
                user = user_result.fetchone()
                if user:
                    print(f"  [권한 부여] {user[0]} ({employee_id})")
                else:
                    print(f"  [권한 부여] 사번 {employee_id}")
            else:
                print(f"  [경고] 사번 {employee_id}에 해당하는 사용자를 찾을 수 없습니다.")
        
        db.commit()
        print(f"\n  총 {updated_count}명에게 관리자 권한 부여 완료")
        
        # 3. 현재 관리자 목록 확인
        print("\n[3단계] 현재 관리자 목록 확인")
        result = db.execute(text("""
            SELECT employee_id, name, email, console_role 
            FROM users 
            WHERE console_role = 1
            ORDER BY employee_id
        """))
        
        admins = result.fetchall()
        if admins:
            print(f"\n  총 {len(admins)}명의 관리자:")
            print(f"  {'사번':<15} {'이름':<15} {'이메일':<30} {'권한':<5}")
            print("  " + "-" * 70)
            for admin in admins:
                print(f"  {admin[0]:<15} {admin[1]:<15} {admin[2]:<30} {'Y':<5}")
        else:
            print("  관리자가 없습니다.")
        
        print("\n" + "=" * 60)
        print("작업 완료!")
        print("=" * 60)
        print("\n관리자 권한 부여/해제 방법:")
        print("  UPDATE users SET console_role = 1 WHERE employee_id = '사번';  -- 권한 부여")
        print("  UPDATE users SET console_role = 0 WHERE employee_id = '사번';  -- 권한 해제")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    add_console_role_column()

