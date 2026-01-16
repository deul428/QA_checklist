"""
users 테이블 백업 및 이메일 변경 스크립트

1. users 테이블을 백업 테이블로 복사
2. 모든 사용자의 email을 테스트 이메일로 변경
3. 나중에 복구할 수 있도록 백업 테이블 유지
"""
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

# 테스트 이메일 주소
TEST_EMAIL = "kimhs@ajnet.co.kr"

def backup_and_update_emails():
    """users 테이블 백업 및 이메일 변경"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("users 테이블 백업 및 이메일 변경")
        print("="*60)
        
        # 1. 백업 테이블 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table_name = f"users_backup_{timestamp}"
        
        print(f"\n[1단계] 백업 테이블 생성: {backup_table_name}")
        db.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {backup_table_name} AS
            SELECT * FROM users
        """))
        db.commit()
        
        # 백업된 행 수 확인
        result = db.execute(text(f"SELECT COUNT(*) FROM {backup_table_name}"))
        backup_count = result.scalar()
        print(f"  백업 완료: {backup_count}개 행")
        
        # 2. 현재 이메일 상태 확인
        print("\n[2단계] 현재 이메일 상태 확인")
        result = db.execute(text("""
            SELECT 
                id,
                employee_id,
                name,
                email
            FROM users
            ORDER BY id
            LIMIT 10
        """))
        
        print("\n  현재 이메일 (처음 10개):")
        print(f"  {'ID':<6} {'사번':<15} {'이름':<15} {'이메일':<30}")
        print("  " + "-"*70)
        for row in result:
            print(f"  {row[0]:<6} {row[1]:<15} {row[2]:<15} {row[3]:<30}")
        
        # 전체 이메일 개수 및 고유 이메일 개수
        result = db.execute(text("SELECT COUNT(*), COUNT(DISTINCT email) FROM users"))
        total_users, unique_emails = result.fetchone()
        print(f"\n  총 사용자 수: {total_users}명")
        print(f"  고유 이메일 수: {unique_emails}개")
        
        # 3. 이메일 변경
        print(f"\n[3단계] 모든 이메일을 테스트 이메일로 변경: {TEST_EMAIL}")
        result = db.execute(text(f"""
            UPDATE users
            SET email = '{TEST_EMAIL}'
        """))
        db.commit()
        updated_count = result.rowcount
        print(f"  변경 완료: {updated_count}개 행")
        
        # 4. 변경 후 상태 확인
        print("\n[4단계] 변경 후 이메일 상태 확인")
        result = db.execute(text("""
            SELECT 
                id,
                employee_id,
                name,
                email
            FROM users
            ORDER BY id
            LIMIT 10
        """))
        
        print("\n  변경된 이메일 (처음 10개):")
        print(f"  {'ID':<6} {'사번':<15} {'이름':<15} {'이메일':<30}")
        print("  " + "-"*70)
        for row in result:
            print(f"  {row[0]:<6} {row[1]:<15} {row[2]:<15} {row[3]:<30}")
        
        # 이메일이 모두 테스트 이메일인지 확인
        result = db.execute(text(f"""
            SELECT COUNT(*) FROM users WHERE email = '{TEST_EMAIL}'
        """))
        test_email_count = result.scalar()
        print(f"\n  테스트 이메일로 변경된 사용자: {test_email_count}명")
        
        print("\n" + "="*60)
        print("백업 및 이메일 변경 완료!")
        print("="*60)
        print(f"\n백업 테이블: {backup_table_name}")
        print(f"테스트 이메일: {TEST_EMAIL}")
        print("\n복구 방법:")
        print(f"  python backend/dummy/restore_user_emails.py {backup_table_name}")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    backup_and_update_emails()

