"""
users 테이블 이메일 복구 스크립트

백업 테이블에서 원래 이메일 주소를 복구합니다.

사용법:
    python backend/dummy/restore_user_emails.py [백업_테이블명]
    
예시:
    python backend/dummy/restore_user_emails.py users_backup_20260115_143000
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

def restore_emails(backup_table_name):
    """백업 테이블에서 원래 이메일 복구"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("users 테이블 이메일 복구")
        print("="*60)
        
        # 백업 테이블 존재 확인
        result = db.execute(text(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{backup_table_name}'
        """))
        if not result.fetchone():
            print(f"\n오류: 백업 테이블 '{backup_table_name}'을 찾을 수 없습니다.")
            print("\n사용 가능한 백업 테이블:")
            result = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'users_backup_%'
                ORDER BY name DESC
            """))
            backups = result.fetchall()
            if backups:
                for backup in backups:
                    print(f"  - {backup[0]}")
            else:
                print("  (백업 테이블이 없습니다)")
            return
        
        # 백업 테이블 행 수 확인
        result = db.execute(text(f"SELECT COUNT(*) FROM {backup_table_name}"))
        backup_count = result.scalar()
        print(f"\n백업 테이블: {backup_table_name}")
        print(f"백업된 행 수: {backup_count}개")
        
        # 현재 users 테이블 행 수 확인
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        current_count = result.scalar()
        print(f"현재 users 테이블 행 수: {current_count}개")
        
        if backup_count != current_count:
            print("\n경고: 백업 테이블과 현재 테이블의 행 수가 다릅니다!")
            response = input("계속하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("복구를 취소했습니다.")
                return
        
        # 복구 전 현재 상태 확인
        print("\n[1단계] 복구 전 현재 이메일 상태 확인")
        result = db.execute(text("""
            SELECT 
                id,
                employee_id,
                name,
                email
            FROM users
            ORDER BY id
            LIMIT 5
        """))
        
        print("\n  현재 이메일 (처음 5개):")
        print(f"  {'ID':<6} {'사번':<15} {'이름':<15} {'이메일':<30}")
        print("  " + "-"*70)
        for row in result:
            print(f"  {row[0]:<6} {row[1]:<15} {row[2]:<15} {row[3]:<30}")
        
        # 복구 실행
        print("\n[2단계] 이메일 복구 실행...")
        result = db.execute(text(f"""
            UPDATE users
            SET email = (
                SELECT email 
                FROM {backup_table_name} 
                WHERE {backup_table_name}.id = users.id
            )
            WHERE EXISTS (
                SELECT 1 
                FROM {backup_table_name} 
                WHERE {backup_table_name}.id = users.id
            )
        """))
        db.commit()
        restored_count = result.rowcount
        print(f"  복구 완료: {restored_count}개 행")
        
        # 복구 후 상태 확인
        print("\n[3단계] 복구 후 이메일 상태 확인")
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
        
        print("\n  복구된 이메일 (처음 10개):")
        print(f"  {'ID':<6} {'사번':<15} {'이름':<15} {'이메일':<30}")
        print("  " + "-"*70)
        for row in result:
            print(f"  {row[0]:<6} {row[1]:<15} {row[2]:<15} {row[3]:<30}")
        
        # 고유 이메일 개수 확인
        result = db.execute(text("SELECT COUNT(DISTINCT email) FROM users"))
        unique_emails = result.scalar()
        print(f"\n  고유 이메일 수: {unique_emails}개")
        
        print("\n" + "="*60)
        print("이메일 복구 완료!")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python backend/dummy/restore_user_emails.py [백업_테이블명]")
        print("\n사용 가능한 백업 테이블 확인:")
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'users_backup_%'
                ORDER BY name DESC
            """))
            backups = result.fetchall()
            if backups:
                for backup in backups:
                    print(f"  - {backup[0]}")
            else:
                print("  (백업 테이블이 없습니다)")
        finally:
            db.close()
        sys.exit(1)
    
    backup_table_name = sys.argv[1]
    restore_emails(backup_table_name)

