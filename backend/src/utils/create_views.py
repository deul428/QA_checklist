"""데이터베이스 조회 편의를 위한 VIEW 생성 스크립트

user_id와 함께 사용자 이름, 사번 등을 함께 볼 수 있는 VIEW를 생성합니다.
"""
import sys
from pathlib import Path
from sqlalchemy import text

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import engine

def create_views():
    """조회 편의를 위한 VIEW 생성"""
    print("=" * 60)
    print("데이터베이스 VIEW 생성")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # 1. checklist_records_view: 체크리스트 기록 + 사용자 정보
            print("\n[1] checklist_records_view 생성")
            print("-" * 60)
            try:
                conn.execute(text("""
                    CREATE VIEW IF NOT EXISTS checklist_records_view AS
                    SELECT 
                        cr.records_id,
                        cr.user_id,
                        u.user_id,
                        u.user_name,
                        u.user_email,
                        cr.check_item_id,
                        ci.item_name,
                        ci.system_id,
                        s.system_name,
                        cr.check_date,
                        cr.status,
                        cr.fail_notes,
                        cr.checked_at
                    FROM checklist_records cr
                    LEFT JOIN users u ON cr.user_id = u.user_id
                    LEFT JOIN check_items ci ON cr.check_item_id = ci.item_id
                    LEFT JOIN systems s ON ci.system_id = s.system_id
                """))
                conn.commit()
                print("  성공: checklist_records_view가 생성되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            # 2. user_system_assignments_view: 사용자-시스템 할당 + 사용자/시스템/체크 항목 정보
            print("\n[2] user_system_assignments_view 생성")
            print("-" * 60)
            try:
                conn.execute(text("""
                    CREATE VIEW IF NOT EXISTS user_system_assignments_view AS
                    SELECT 
                        usa.assign_id AS id,
                        usa.user_id,
                        u.user_id,
                        u.user_name,
                        u.user_email,
                        u.division,
                        u.general_headquarters,
                        u.department,
                        u.position,
                        u.role,
                        usa.system_id,
                        s.system_name,
                        s.system_description,
                        usa.item_id,
                        ci.item_name,
                        ci.item_description,
                        usa.created_at
                    FROM user_system_assignments usa
                    LEFT JOIN users u ON usa.user_id = u.user_id
                    LEFT JOIN systems s ON usa.system_id = s.system_id
                    LEFT JOIN check_items ci ON usa.item_id = ci.item_id
                """))
                conn.commit()
                print("  성공: user_system_assignments_view가 생성되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            # 3. check_items_view: 체크 항목 + 시스템 정보
            print("\n[3] check_items_view 생성")
            print("-" * 60)
            try:
                conn.execute(text("""
                    CREATE VIEW IF NOT EXISTS check_items_view AS
                    SELECT 
                        ci.item_id AS id,
                        ci.system_id,
                        s.system_name,
                        s.system_description,
                        ci.item_name,
                        ci.item_description,
                        ci.status,
                        ci.created_at
                    FROM check_items ci
                    LEFT JOIN systems s ON ci.system_id = s.system_id
                """))
                conn.commit()
                print("  성공: check_items_view가 생성되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            # 4. user_system_assignments_with_items_view: 사용자-시스템 할당 + 체크 항목 정보
            print("\n[4] user_system_assignments_with_items_view 생성")
            print("-" * 60)
            try:
                conn.execute(text("""
                    CREATE VIEW IF NOT EXISTS user_system_assignments_with_items_view AS
                    SELECT 
                        usa.assign_id AS assignment_id,
                        usa.user_id,
                        u.user_id,
                        u.user_name,
                        u.user_email,
                        u.division,
                        u.general_headquarters,
                        u.department,
                        u.position,
                        u.role,
                        usa.system_id,
                        s.system_name,
                        s.system_description,
                        usa.item_id AS check_item_id,
                        ci.item_name,
                        ci.item_description,
                        usa.created_at AS assigned_at
                    FROM user_system_assignments usa
                    LEFT JOIN users u ON usa.user_id = u.user_id
                    LEFT JOIN systems s ON usa.system_id = s.system_id
                    LEFT JOIN check_items ci ON usa.item_id = ci.item_id
                    ORDER BY usa.user_id, usa.system_id, usa.item_id
                """))
                conn.commit()
                print("  성공: user_system_assignments_with_items_view가 생성되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            # 5. system_check_items_assignments_view: 시스템별 체크 항목의 담당자 리스트 (GUI 조회용)
            print("\n[5] system_check_items_assignments_view 생성")
            print("-" * 60)
            try:
                conn.execute(text("""
                    CREATE VIEW IF NOT EXISTS system_check_items_assignments_view AS
                    SELECT 
                        s.system_id,
                        s.system_name,
                        ci.item_id AS check_item_id,
                        ci.item_name,
                        usa.assign_id,
                        u.user_id,
                        u.user_name,
                        usa.created_at AS assigned_at
                    FROM systems s
                    INNER JOIN check_items ci ON s.system_id = ci.system_id
                    LEFT JOIN user_system_assignments usa ON ci.item_id = usa.item_id
                    LEFT JOIN users u ON usa.user_id = u.user_id
                    WHERE ci.status = 'active'
                    ORDER BY s.system_id, ci.item_id, u.user_name
                """))
                conn.commit()
                print("  성공: system_check_items_assignments_view가 생성되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            print("\n" + "=" * 60)
            print("VIEW 생성 완료!")
            print("=" * 60)
            print("\n사용 예시:")
            print("  SELECT * FROM checklist_records_view;")
            print("  SELECT * FROM user_system_assignments_view;")
            print("  SELECT * FROM check_items_view;")
            print("  SELECT * FROM system_check_items_assignments_view;")
            print("\n시스템별 담당자 조회 예시:")
            print("  SELECT * FROM system_check_items_assignments_view WHERE system_id = 1;")
            print("  SELECT * FROM system_check_items_assignments_view WHERE system_name = 'IAS Sales';")
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_views()

