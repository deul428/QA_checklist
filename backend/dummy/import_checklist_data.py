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
    python backend/dummy/import_checklist_data.py [CSV 파일 경로]
    
    CSV 파일 경로를 지정하지 않으면 database/checklist_data_0115_bom.csv를 사용합니다.
"""
import sys
import csv
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import System, CheckItem, User, UserSystemAssignment

# 기본 CSV 파일 경로
DEFAULT_CSV_FILE = project_root / "database" / "checklist_data_0115_bom.csv"


def import_checklist_data(csv_file_path=None):
    """CSV 파일에서 체크리스트 데이터를 읽어 데이터베이스에 import"""
    db: Session = SessionLocal()
    
    try:
        # CSV 파일 경로 결정
        if csv_file_path:
            csv_file = Path(csv_file_path)
        else:
            csv_file = DEFAULT_CSV_FILE
        
        if not csv_file.exists():
            print(f"오류: CSV 파일을 찾을 수 없습니다: {csv_file}")
            return
        
        print(f"CSV 파일 읽기: {csv_file}")
        
        # 기존 데이터 삭제 여부 확인
        print("\n[주의] 기존 데이터를 삭제하고 새로 import합니다.")
        print("   - 기존 check_items 데이터 삭제")
        print("   - 기존 user_system_assignments 데이터 삭제")
        print("   - systems 데이터는 유지 (이름으로 매칭)")
        
        # 기존 데이터 삭제
        db.query(CheckItem).delete()
        db.query(UserSystemAssignment).delete()
        db.commit()
        print("   기존 데이터 삭제 완료\n")
        
        systems_map = {}  # {system_name: System 객체}
        check_items_map = {}  # {(system_name, item_name): CheckItem 객체}
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            # CSV 파서 설정: 여러 행에 걸친 필드 처리
            reader = csv.DictReader(f)
            
            systems_created = 0
            items_created = 0
            items_updated = 0
            assignments_created = 0
            skipped_count = 0
            total_csv_rows = 0
            
            # 체크 항목을 먼저 수집 (중복 제거)
            items_data = {}  # {(system_name, item_name): {description, order_index, item_id}}
            user_item_relations = []  # [(user_name, system_name, item_name)]
            
            for row_num, row in enumerate(reader, start=2):
                total_csv_rows += 1
                # 필수 필드 확인
                user_name = row.get('user_name', '').strip()
                system_name = row.get('system_id', '').strip()
                item_name = row.get('item_name', '').strip()
                
                if not system_name or not item_name:
                    print(f"  [건너뜀] {row_num}행: 필수 필드 누락 (시스템={system_name}, 항목={item_name})")
                    skipped_count += 1
                    continue
                
                # 체크 항목 데이터 수집 (중복 제거)
                item_key = (system_name, item_name)
                if item_key not in items_data:
                    description = row.get('description', '').strip() or None
                    order_index_str = row.get('order_index', '').strip()
                    item_id_str = row.get('id', '').strip()
                    
                    try:
                        order_index = int(order_index_str) if order_index_str else None
                    except:
                        order_index = None
                    
                    items_data[item_key] = {
                        'description': description,
                        'order_index': order_index,
                        'item_id': item_id_str
                    }
                
                # 사용자-항목 관계 저장
                if user_name:
                    user_item_relations.append((user_name, system_name, item_name))
            
            # 1단계: 시스템 생성/매칭
            for system_name in set(key[0] for key in items_data.keys()):
                if system_name not in systems_map:
                    system = db.query(System).filter(System.system_name == system_name).first()
                    if not system:
                        system = System(system_name=system_name)
                        db.add(system)
                        db.flush()
                        systems_created += 1
                        print(f"  [시스템 생성] {system_name} (ID: {system.id})")
                    systems_map[system_name] = system
            
            # 2단계: 체크 항목 생성/업데이트
            for (system_name, item_name), item_data in items_data.items():
                system = systems_map[system_name]
                
                # 기존 항목 확인 (시스템과 항목 이름으로)
                existing_item = db.query(CheckItem).join(System).filter(
                    System.system_name == system_name,
                    CheckItem.item_name == item_name.strip()
                ).first()
                
                if existing_item:
                    # 기존 항목 업데이트
                    if item_data['description']:
                        existing_item.description = item_data['description']
                    if item_data['order_index']:
                        existing_item.order_index = item_data['order_index']
                    check_items_map[(system_name, item_name)] = existing_item
                    items_updated += 1
                else:
                    # 새 항목 생성
                    order_index = item_data['order_index']
                    if not order_index:
                        existing_count = db.query(CheckItem).filter(
                            CheckItem.system_id == system.id
                        ).count()
                        order_index = existing_count + 1
                    
                    check_item = CheckItem(
                        system_id=system.id,
                        item_name=item_name.strip(),
                        description=item_data['description'],
                        order_index=order_index
                    )
                    db.add(check_item)
                    db.flush()
                    check_items_map[(system_name, item_name)] = check_item
                    items_created += 1
                    try:
                        print(f"  [항목 생성] {system_name} > {item_name[:30]}... (ID: {check_item.id})")
                    except:
                        print(f"  [항목 생성] system_id: {system.id}, order: {order_index}")
            
            db.flush()  # 항목들을 먼저 저장
            
            # 3단계: 사용자-시스템-항목 할당 (각 항목마다 별도 행으로 저장)
            assignment_set = set()  # 중복 방지용
            for user_name, system_name, item_name in user_item_relations:
                if not user_name or not system_name or not item_name:
                    continue
                
                # 사용자 조회
                user = db.query(User).filter(User.name == user_name.strip()).first()
                if not user:
                    print(f"    [경고] 사용자를 찾을 수 없습니다: {user_name}")
                    continue
                
                system = systems_map.get(system_name)
                if not system:
                    continue
                
                # 중복 방지 (user_id, system_id, item_name 조합)
                assignment_key = (user.id, system.id, item_name.strip())
                if assignment_key not in assignment_set:
                    # 기존 할당 확인
                    existing_assignment = db.query(UserSystemAssignment).filter(
                        UserSystemAssignment.user_id == user.id,
                        UserSystemAssignment.system_id == system.id,
                        UserSystemAssignment.item_name == item_name.strip()
                    ).first()
                    
                    if not existing_assignment:
                        assignment = UserSystemAssignment(
                            user_id=user.id,
                            user_name=user.name,
                            system_id=system.id,
                            item_name=item_name.strip()
                        )
                        db.add(assignment)
                        assignments_created += 1
                        assignment_set.add(assignment_key)
                        try:
                            print(f"    [할당] {user_name} -> {system_name} > {item_name[:30]}...")
                        except:
                            print(f"    [할당] user_id: {user.id} -> system_id: {system.id}, item: {item_name[:30]}")
            
            db.commit()
            
            print("\n" + "="*60)
            print("Import 완료!")
            print(f"  CSV 총 행 수: {total_csv_rows}개")
            print(f"  새로 생성된 시스템: {systems_created}개")
            print(f"  새로 생성된 체크 항목: {items_created}개")
            print(f"  업데이트된 체크 항목: {items_updated}개")
            print(f"  새로 생성된 담당자 할당: {assignments_created}개")
            print(f"  건너뜀: {skipped_count}개")
            print("="*60)
            
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    import_checklist_data(csv_file)

