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
                        cr.id,
                        cr.user_id,
                        u.employee_id,
                        u.name AS user_name,
                        u.email AS user_email,
                        cr.check_item_id,
                        ci.item_name,
                        ci.system_id,
                        s.system_name,
                        cr.check_date,
                        cr.status,
                        cr.notes,
                        cr.checked_at
                    FROM checklist_records cr
                    LEFT JOIN users u ON cr.user_id = u.id
                    LEFT JOIN check_items ci ON cr.check_item_id = ci.id
                    LEFT JOIN systems s ON ci.system_id = s.id
                """))
                conn.commit()
                print("  성공: checklist_records_view가 생성되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            # 2. user_system_assignments_view: 사용자-시스템 할당 + 사용자/시스템 정보
            print("\n[2] user_system_assignments_view 생성")
            print("-" * 60)
            try:
                conn.execute(text("""
                    CREATE VIEW IF NOT EXISTS user_system_assignments_view AS
                    SELECT 
                        usa.id,
                        usa.user_id,
                        u.employee_id,
                        u.name AS user_name,
                        u.email AS user_email,
                        u.division,
                        u.general_headquarters,
                        u.department,
                        u.position,
                        u.role,
                        usa.system_id,
                        s.system_name,
                        s.description AS system_description,
                        usa.created_at
                    FROM user_system_assignments usa
                    LEFT JOIN users u ON usa.user_id = u.id
                    LEFT JOIN systems s ON usa.system_id = s.id
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
                        ci.id,
                        ci.system_id,
                        s.system_name,
                        s.description AS system_description,
                        ci.item_name,
                        ci.description,
                        ci.order_index,
                        ci.created_at
                    FROM check_items ci
                    LEFT JOIN systems s ON ci.system_id = s.id
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
                        usa.id AS assignment_id,
                        usa.user_id,
                        u.employee_id,
                        u.name AS user_name,
                        u.email AS user_email,
                        u.division,
                        u.general_headquarters,
                        u.department,
                        u.position,
                        u.role,
                        usa.system_id,
                        s.system_name,
                        s.description AS system_description,
                        ci.id AS check_item_id,
                        ci.item_name,
                        ci.description AS item_description,
                        ci.order_index,
                        usa.created_at AS assigned_at
                    FROM user_system_assignments usa
                    LEFT JOIN users u ON usa.user_id = u.id
                    LEFT JOIN systems s ON usa.system_id = s.id
                    LEFT JOIN check_items ci ON usa.system_id = ci.system_id
                    ORDER BY usa.user_id, usa.system_id, ci.order_index
                """))
                conn.commit()
                print("  성공: user_system_assignments_with_items_view가 생성되었습니다.")
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
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_views()

