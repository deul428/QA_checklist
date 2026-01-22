"""
check_items 테이블에서 environment 컬럼 제거 마이그레이션 스크립트

1. 같은 system_id, item_name을 가진 항목들을 하나로 통합
2. checklist_records, user_system_assignments, checklist_records_logs의 item_id 참조 업데이트
3. 중복 항목 삭제
"""
import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import CheckItem, ChecklistRecord, UserSystemAssignment, ChecklistRecordLog

def migrate_remove_environment_from_check_items():
    """check_items에서 environment 제거 마이그레이션"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("check_items에서 environment 제거 마이그레이션 시작")
        print("=" * 60)
        print()
        
        # 통계 변수
        total_groups = 0
        total_items_merged = 0
        total_items_deleted = 0
        total_records_updated = 0
        total_assignments_updated = 0
        total_logs_updated = 0
        
        # 1. 항목 그룹화: 같은 system_id, item_name을 가진 항목들 찾기
        print("1. 항목 그룹화 중...")
        all_items = db.query(CheckItem).all()
        
        # 그룹화: (system_id, item_name) -> [items]
        item_groups = defaultdict(list)
        for item in all_items:
            key = (item.system_id, item.item_name)
            item_groups[key].append(item)
        
        # 여러 환경에 걸친 항목 그룹만 필터링
        groups_to_merge = {k: v for k, v in item_groups.items() if len(v) > 1}
        total_groups = len(groups_to_merge)
        
        print(f"   총 {len(all_items)}개의 항목 중 {total_groups}개의 그룹이 통합 대상입니다.")
        print()
        
        if total_groups == 0:
            print("[OK] 통합할 항목이 없습니다. 마이그레이션이 완료되었습니다.")
            return
        
        # 2. 각 그룹별로 통합 수행
        print("2. 항목 통합 및 참조 업데이트 중...")
        print()
        
        for (system_id, item_name), items in groups_to_merge.items():
            # 통합 기준 항목 선택: prd 우선, 없으면 가장 오래된 항목
            target_item = None
            for item in items:
                if item.environment == "prd":
                    target_item = item
                    break
            
            if not target_item:
                # prd가 없으면 가장 오래된 항목 선택
                target_item = min(items, key=lambda x: x.item_id)
            
            print(f"   [그룹] 시스템 ID {system_id}, 항목명: '{item_name}'")
            print(f"      통합 기준 항목 ID: {target_item.item_id} (환경: {target_item.environment})")
            
            # 통합할 항목들 (기준 항목 제외)
            items_to_merge = [item for item in items if item.item_id != target_item.item_id]
            
            if not items_to_merge:
                print(f"      [SKIP] 통합할 항목이 없습니다.")
                print()
                continue
            
            print(f"      통합 대상: {len(items_to_merge)}개 항목")
            
            # 3. 참조 업데이트
            for item in items_to_merge:
                old_item_id = item.item_id
                new_item_id = target_item.item_id
                
                # checklist_records 업데이트
                records_updated = db.execute(
                    text("""
                        UPDATE checklist_records
                        SET item_id = :new_item_id
                        WHERE item_id = :old_item_id
                    """),
                    {"new_item_id": new_item_id, "old_item_id": old_item_id}
                ).rowcount
                total_records_updated += records_updated
                
                # user_system_assignments 업데이트
                assignments_updated = db.execute(
                    text("""
                        UPDATE user_system_assignments
                        SET item_id = :new_item_id
                        WHERE item_id = :old_item_id
                    """),
                    {"new_item_id": new_item_id, "old_item_id": old_item_id}
                ).rowcount
                total_assignments_updated += assignments_updated
                
                # checklist_records_logs 업데이트
                logs_updated = db.execute(
                    text("""
                        UPDATE checklist_records_logs
                        SET check_item_id = :new_item_id
                        WHERE check_item_id = :old_item_id
                    """),
                    {"new_item_id": new_item_id, "old_item_id": old_item_id}
                ).rowcount
                total_logs_updated += logs_updated
                
                print(f"         항목 ID {old_item_id} → {new_item_id}: "
                      f"records {records_updated}개, assignments {assignments_updated}개, logs {logs_updated}개 업데이트")
            
            # 4. 중복 항목 삭제
            for item in items_to_merge:
                db.delete(item)
                total_items_deleted += 1
            
            total_items_merged += len(items_to_merge)
            print()
        
        # 커밋
        db.commit()
        
        # 5. 최종 리포트
        print("=" * 60)
        print("마이그레이션 완료")
        print("=" * 60)
        print(f"통합된 그룹 수: {total_groups}개")
        print(f"통합된 항목 수: {total_items_merged}개")
        print(f"삭제된 항목 수: {total_items_deleted}개")
        print(f"업데이트된 checklist_records: {total_records_updated}개")
        print(f"업데이트된 user_system_assignments: {total_assignments_updated}개")
        print(f"업데이트된 checklist_records_logs: {total_logs_updated}개")
        print()
        
        # 6. 남은 항목 수 확인
        remaining_items = db.query(CheckItem).count()
        print(f"남은 항목 수: {remaining_items}개")
        print()
        
        print("[OK] 데이터 마이그레이션이 완료되었습니다!")
        print()
        print("[다음 단계]")
        print("1. 데이터베이스에서 check_items 테이블의 environment 컬럼을 제거하세요.")
        print("2. UniqueConstraint를 (system_id, item_name)으로 변경하세요.")
        print("3. CheckConstraint에서 environment 관련 제약을 제거하세요.")
        print("4. 코드 업데이트를 진행하세요.")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_remove_environment_from_check_items()

