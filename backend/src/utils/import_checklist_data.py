"""
체크리스트 데이터 import 스크립트

CSV 형식:
user_name, id, system_id, item_name, description, order_index, created_at

각 행은 사용자-체크 항목 관계를 나타냅니다.
같은 체크 항목에 여러 사용자가 담당할 수 있으며, 각 사용자마다 별도 행으로 저장됩니다.

예시:
김지훈, 2, IAS Sales, CPU 사용률 95% 이상 사용여부 확인, , 2, 2026년 1월 14일 수요일
김정민, 2, IAS Sales, CPU 사용률 95% 이상 사용여부 확인, , 2, 2026년 1월 14일 수요일

사용법:
    python backend/src/utils/import_checklist_data.py [CSV 파일 경로]
    
    CSV 파일 경로를 지정하지 않으면 database/checklist_data_0115_bom.csv를 사용합니다.
"""
import sys
import csv
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import System, CheckItem, User, UserSystemAssignment

# 기본 CSV 파일 경로
DEFAULT_CSV_FILE = project_root / "database" / "checklist_data_0115_bom.csv"


def import_checklist_data(csv_file_path=None):
    """
    CSV 파일에서 체크리스트 데이터를 읽어 데이터베이스에 import
    
    Args:
        csv_file_path: CSV 파일 경로 (지정하지 않으면 기본값 사용)
    """
    if csv_file_path is None:
        csv_file_path = DEFAULT_CSV_FILE
    else:
        csv_file_path = Path(csv_file_path)
    
    if not csv_file_path.exists():
        print(f"오류: CSV 파일을 찾을 수 없습니다: {csv_file_path}")
        return
    
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("체크리스트 데이터 Import 시작")
        print("=" * 60)
        print(f"CSV 파일: {csv_file_path}")
        
        # 기존 데이터 삭제
        print("\n[1] 기존 체크 항목 및 할당 데이터 삭제 중...")
        db.query(UserSystemAssignment).delete()
        db.query(CheckItem).delete()
        db.commit()
        print("기존 데이터 삭제 완료")
        
        # CSV 파일 읽기
        print("\n[2] CSV 파일 읽기 중...")
        systems = {}  # {system_name: System 객체}
        check_items = {}  # {(system_id, item_name): CheckItem 객체}
        user_assignments = []  # [(user_id, system_id, item_name), ...]
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader, start=2):
                try:
                    # CSV 필드 파싱
                    user_names_str = row.get('user_name', '').strip()
                    system_name = row.get('system_id', '').strip()
                    item_name = row.get('item_name', '').strip()
                    description = row.get('description', '').strip()
                    order_index_str = row.get('order_index', '').strip()
                    
                    if not system_name or not item_name:
                        print(f"경고: {row_idx}행 - 시스템명 또는 항목명이 비어있습니다. 건너뜁니다.")
                        continue
                    
                    # 시스템 생성 또는 조회
                    if system_name not in systems:
                        system = System(system_name=system_name)
                        db.add(system)
                        db.flush()  # ID 생성
                        systems[system_name] = system
                        print(f"시스템 생성: {system_name} (ID: {system.id})")
                    
                    system = systems[system_name]
                    
                    # 체크 항목 생성 또는 조회
                    item_key = (system.id, item_name)
                    if item_key not in check_items:
                        order_index = int(order_index_str) if order_index_str else 0
                        check_item = CheckItem(
                            system_id=system.id,
                            item_name=item_name,
                            description=description if description else None,
                            order_index=order_index
                        )
                        db.add(check_item)
                        db.flush()  # ID 생성
                        check_items[item_key] = check_item
                        print(f"체크 항목 생성: {item_name} (시스템: {system_name})")
                    
                    # 사용자 할당 정보 수집
                    if user_names_str:
                        user_names = [name.strip() for name in user_names_str.split(',') if name.strip()]
                        for user_name in user_names:
                            user_assignments.append((user_name, system.id, item_name))
                
                except Exception as e:
                    print(f"오류: {row_idx}행 처리 중 오류 발생: {e}")
                    continue
        
        db.commit()
        print(f"\n[3] 시스템 및 체크 항목 생성 완료")
        print(f"  - 시스템 수: {len(systems)}")
        print(f"  - 체크 항목 수: {len(check_items)}")
        
        # 사용자 할당 생성
        print("\n[4] 사용자 할당 생성 중...")
        assignment_count = 0
        skipped_count = 0
        
        for user_name, system_id, item_name in user_assignments:
            try:
                # 사용자 조회
                user = db.query(User).filter(User.name == user_name).first()
                if not user:
                    print(f"경고: 사용자를 찾을 수 없습니다: {user_name}")
                    skipped_count += 1
                    continue
                
                # 체크 항목 조회
                check_item = check_items.get((system_id, item_name))
                if not check_item:
                    print(f"경고: 체크 항목을 찾을 수 없습니다: {item_name} (시스템 ID: {system_id})")
                    skipped_count += 1
                    continue
                
                # 할당 생성 (중복 체크)
                existing = db.query(UserSystemAssignment).filter(
                    UserSystemAssignment.user_id == user.id,
                    UserSystemAssignment.system_id == system_id,
                    UserSystemAssignment.item_name == item_name
                ).first()
                
                if not existing:
                    assignment = UserSystemAssignment(
                        user_id=user.id,
                        system_id=system_id,
                        item_name=item_name,
                        user_name=user.name
                    )
                    db.add(assignment)
                    assignment_count += 1
            
            except Exception as e:
                print(f"오류: 사용자 할당 생성 중 오류 발생 ({user_name}, {item_name}): {e}")
                skipped_count += 1
                continue
        
        db.commit()
        print(f"\n[5] 사용자 할당 생성 완료")
        print(f"  - 생성된 할당 수: {assignment_count}")
        print(f"  - 건너뛴 할당 수: {skipped_count}")
        
        print("\n" + "=" * 60)
        print("체크리스트 데이터 Import 완료!")
        print("=" * 60)
    
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    csv_file = None
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    import_checklist_data(csv_file)

