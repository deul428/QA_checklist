"""console fail-items API 디버깅 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import ChecklistRecordLog, CheckItem, System, User
from services.scheduler import get_korea_today

def debug_console_fail_items():
    """console fail-items API 로직 디버깅"""
    db: Session = SessionLocal()
    
    try:
        print("="*60)
        print("Console fail-items API 디버깅")
        print("="*60)
        
        today = get_korea_today()
        print(f"\n오늘 날짜: {today}")
        
        # 오늘 날짜의 모든 로그 조회
        all_logs = (
            db.query(ChecklistRecordLog)
            .filter(ChecklistRecordLog.check_date == today)
            .order_by(ChecklistRecordLog.check_item_id, ChecklistRecordLog.created_at)
            .all()
        )
        
        print(f"\n전체 로그 수: {len(all_logs)}개")
        print("\n로그 상세:")
        for log in all_logs:
            print(f"  id={log.id}, check_item_id={log.check_item_id}, status={log.status}, action={log.action}, created_at={log.created_at}, notes={log.notes}")
        
        # 각 check_item_id별로 상태 변경 추적
        item_status_history = {}
        
        for log in all_logs:
            if log.check_item_id not in item_status_history:
                item_status_history[log.check_item_id] = []
            item_status_history[log.check_item_id].append((
                log.status,
                log.created_at,
                log.user_id,
                log.notes
            ))
        
        print(f"\n항목별 상태 이력: {len(item_status_history)}개 항목")
        for check_item_id, history in item_status_history.items():
            print(f"\n  check_item_id={check_item_id}:")
            for i, (status, created_at, user_id, notes) in enumerate(history):
                print(f"    [{i+1}] status={status}, time={created_at}, user_id={user_id}, notes={notes}")
            final_status = history[-1][0]
            print(f"    최종 상태: {final_status}")
        
        # 최종 상태가 FAIL인 항목 찾기
        fail_items = []
        for check_item_id, history in item_status_history.items():
            final_status = history[-1][0]
            if final_status == "FAIL":
                # 첫 번째 FAIL 로그 찾기
                first_fail_log = None
                for status, created_at, user_id, notes in history:
                    if status == "FAIL":
                        first_fail_log = (status, created_at, user_id, notes)
                        break
                
                if first_fail_log:
                    check_item = db.query(CheckItem).filter(CheckItem.id == check_item_id).first()
                    if check_item:
                        system = db.query(System).filter(System.id == check_item.system_id).first()
                        user = db.query(User).filter(User.id == first_fail_log[2]).first()
                        if system and user:
                            fail_items.append({
                                "check_item_id": check_item_id,
                                "item_name": check_item.item_name,
                                "system_name": system.system_name,
                                "user_name": user.name,
                                "first_fail_time": first_fail_log[1],
                                "notes": first_fail_log[3]
                            })
        
        print(f"\n최종 FAIL 항목: {len(fail_items)}개")
        for item in fail_items:
            print(f"  - {item['item_name']} (시스템: {item['system_name']}, 담당자: {item['user_name']}, 시간: {item['first_fail_time']})")
        
        # checklist_records 테이블에서도 확인
        from models.models import ChecklistRecord
        from datetime import date
        today_date = date.today()
        fail_records = (
            db.query(ChecklistRecord)
            .filter(
                ChecklistRecord.check_date == today_date,
                ChecklistRecord.status == "FAIL"
            )
            .all()
        )
        print(f"\nchecklist_records 테이블의 FAIL 레코드: {len(fail_records)}개")
        for record in fail_records:
            check_item = db.query(CheckItem).filter(CheckItem.id == record.check_item_id).first()
            if check_item:
                print(f"  - check_item_id={record.check_item_id}, item_name={check_item.item_name}, checked_at={record.checked_at}")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    debug_console_fail_items()

