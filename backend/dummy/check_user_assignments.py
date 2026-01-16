"""user_system_assignments 데이터 점검 스크립트"""
import sys
from pathlib import Path
from sqlalchemy import text

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import SessionLocal, engine
from models.models import User, System, UserSystemAssignment, CheckItem

def check_user_assignments():
    """user_system_assignments 데이터 점검"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("user_system_assignments 데이터 점검")
        print("=" * 80)
        
        # VIEW를 사용하여 데이터 조회
        print("\n[1] user_system_assignments_view로 전체 데이터 조회")
        print("-" * 80)
        
        result = db.execute(text("""
            SELECT 
                id,
                user_id,
                employee_id,
                user_name,
                system_id,
                system_name
            FROM user_system_assignments_view
            ORDER BY user_name, system_name
        """))
        
        assignments = result.fetchall()
        
        if not assignments:
            print("  데이터가 없습니다.")
        else:
            print(f"\n총 {len(assignments)}개의 할당이 있습니다.\n")
            print(f"{'ID':<6} {'사용자':<15} {'사번':<10} {'시스템':<30}")
            print("-" * 80)
            
            for row in assignments:
                assign_id = row[0] or "NULL"
                user_id = row[1] or "NULL"
                employee_id = row[2] or "NULL"
                user_name = row[3] or "NULL"
                system_id = row[4] or "NULL"
                system_name = row[5] or "NULL"
                
                try:
                    print(f"{assign_id:<6} {user_name:<15} {employee_id:<10} {system_name:<30}")
                except:
                    print(f"id={assign_id}, user_id={user_id}, system_id={system_id}")
        
        # 시스템별 담당자 목록
        print("\n\n[2] 시스템별 담당자 목록")
        print("-" * 80)
        
        result = db.execute(text("""
            SELECT 
                system_name,
                GROUP_CONCAT(user_name, ', ') as responsible_users,
                COUNT(DISTINCT user_id) as user_count
            FROM user_system_assignments_view
            GROUP BY system_id, system_name
            ORDER BY system_name
        """))
        
        systems = result.fetchall()
        
        for row in systems:
            system_name = row[0] or "NULL"
            users = row[1] or "없음"
            user_count = row[2] or 0
            
            try:
                print(f"\n{system_name} ({user_count}명):")
                print(f"  담당자: {users}")
            except:
                print(f"system_id={row[0]}, user_count={user_count}")
        
        # 사용자별 담당 시스템 목록
        print("\n\n[3] 사용자별 담당 시스템 목록")
        print("-" * 80)
        
        result = db.execute(text("""
            SELECT 
                user_name,
                employee_id,
                GROUP_CONCAT(system_name, ', ') as systems,
                COUNT(DISTINCT system_id) as system_count
            FROM user_system_assignments_view
            GROUP BY user_id, user_name, employee_id
            ORDER BY user_name
        """))
        
        users = result.fetchall()
        
        for row in users:
            user_name = row[0] or "NULL"
            employee_id = row[1] or "NULL"
            systems = row[2] or "없음"
            system_count = row[3] or 0
            
            try:
                print(f"\n{user_name} ({employee_id}) - {system_count}개 시스템:")
                print(f"  {systems}")
            except:
                print(f"user_id={row[0]}, system_count={system_count}")
        
        # 문제점 확인
        print("\n\n[4] 문제점 확인")
        print("-" * 80)
        
        # 1. 시스템에 체크 항목은 있지만 담당자가 없는 경우
        result = db.execute(text("""
            SELECT DISTINCT s.id, s.system_name, COUNT(ci.id) as item_count
            FROM systems s
            LEFT JOIN check_items ci ON s.id = ci.system_id
            LEFT JOIN user_system_assignments usa ON s.id = usa.system_id
            WHERE ci.id IS NOT NULL AND usa.id IS NULL
            GROUP BY s.id, s.system_name
        """))
        
        orphaned_systems = result.fetchall()
        if orphaned_systems:
            print("\n[경고] 체크 항목은 있지만 담당자가 없는 시스템:")
            for row in orphaned_systems:
                print(f"  - {row[1]} (항목 {row[2]}개)")
        else:
            print("\n[확인] 모든 시스템에 담당자가 있습니다.")
        
        # 2. 담당자는 있지만 체크 항목이 없는 시스템
        result = db.execute(text("""
            SELECT DISTINCT s.id, s.system_name, COUNT(DISTINCT usa.user_id) as user_count
            FROM systems s
            INNER JOIN user_system_assignments usa ON s.id = usa.system_id
            LEFT JOIN check_items ci ON s.id = ci.system_id
            WHERE ci.id IS NULL
            GROUP BY s.id, s.system_name
        """))
        
        empty_systems = result.fetchall()
        if empty_systems:
            print("\n[경고] 담당자는 있지만 체크 항목이 없는 시스템:")
            for row in empty_systems:
                print(f"  - {row[1]} (담당자 {row[2]}명)")
        else:
            print("\n[확인] 모든 시스템에 체크 항목이 있습니다.")
        
        print("\n" + "=" * 80)
        print("점검 완료")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user_assignments()

