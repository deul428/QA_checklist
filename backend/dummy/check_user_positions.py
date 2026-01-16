"""users 테이블의 position과 role 데이터 확인 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from services.database import SessionLocal

def check_positions():
    """position과 role 데이터 확인"""
    db = SessionLocal()
    
    try:
        print("="*60)
        print("users 테이블 position/role 데이터 확인")
        print("="*60)
        
        # position별 통계
        print("\n[1] position별 사용자 수:")
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM users
            WHERE position IS NOT NULL
            GROUP BY position
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}명")
        
        # role별 통계
        print("\n[2] role별 사용자 수:")
        result = db.execute(text("""
            SELECT role, COUNT(*) as count
            FROM users
            WHERE role IS NOT NULL
            GROUP BY role
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}명")
        
        # 본부장 찾기 (position이나 role에 본부장이 포함된 경우)
        print("\n[3] 본부장 후보:")
        result = db.execute(text("""
            SELECT id, employee_id, name, position, role, headquarters, general_headquarters
            FROM users
            WHERE position LIKE '%본부장%' 
               OR role LIKE '%본부장%'
               OR position LIKE '%부장%'
               OR role LIKE '%부장%'
        """))
        for row in result:
            print(f"  {row[2]} ({row[1]}): position={row[3]}, role={row[4]}, 본부={row[5]}, 총괄본부={row[6]}")
        
        # 팀장 찾기
        print("\n[4] 팀장 후보:")
        result = db.execute(text("""
            SELECT id, employee_id, name, position, role, department, headquarters
            FROM users
            WHERE position LIKE '%팀장%' 
               OR role LIKE '%팀장%'
               OR position LIKE '%팀%'
        """))
        for row in result:
            print(f"  {row[2]} ({row[1]}): position={row[3]}, role={row[4]}, 부서={row[5]}, 본부={row[6]}")
        
        # DX본부 사용자 확인
        print("\n[5] DX본부 사용자:")
        result = db.execute(text("""
            SELECT id, employee_id, name, position, role, headquarters
            FROM users
            WHERE headquarters LIKE '%DX%' OR general_headquarters LIKE '%DX%'
            ORDER BY position, role
        """))
        for row in result:
            print(f"  {row[2]} ({row[1]}): position={row[3]}, role={row[4]}, 본부={row[5]}")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_positions()

