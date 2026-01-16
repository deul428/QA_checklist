"""참조자(팀장/본부장) 디버깅 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import User, CheckItem, ChecklistRecord, UserSystemAssignment, System
from datetime import date
import pytz

def get_korea_today():
    """한국 시간 기준 오늘 날짜 반환"""
    kst = pytz.timezone("Asia/Seoul")
    kst_now = pytz.datetime.datetime.now(kst)
    return kst_now.date()

def debug_cc_recipients():
    """참조자 찾기 로직 디버깅"""
    db: Session = SessionLocal()
    
    try:
        print("="*60)
        print("참조자(팀장/본부장) 디버깅")
        print("="*60)
        
        # 오늘 날짜
        today = get_korea_today()
        print(f"\n오늘 날짜: {today}")
        
        # 오늘 체크된 항목
        checked_records = (
            db.query(ChecklistRecord).filter(ChecklistRecord.check_date == today).all()
        )
        checked_item_ids = {r.check_item_id for r in checked_records}
        print(f"체크된 항목 수: {len(checked_item_ids)}")
        
        # 모든 체크 항목
        all_check_items = db.query(CheckItem).all()
        unchecked_items = [
            item for item in all_check_items if item.id not in checked_item_ids
        ]
        print(f"미체크 항목 수: {len(unchecked_items)}")
        
        if not unchecked_items:
            print("미체크 항목이 없습니다.")
            return
        
        # 미체크 항목의 담당자 수집
        responsible_users = set()
        for item in unchecked_items:
            assignments = (
                db.query(UserSystemAssignment)
                .filter(UserSystemAssignment.system_id == item.system_id)
                .all()
            )
            for assignment in assignments:
                user = db.query(User).filter(User.id == assignment.user_id).first()
                if user:
                    responsible_users.add(user)
        
        print(f"\n담당자 수: {len(responsible_users)}명")
        print("\n담당자 정보:")
        for user in responsible_users:
            print(f"  {user.name} ({user.employee_id}): 부서={user.department}, 본부={user.headquarters}, 총괄본부={user.general_headquarters}, 직위={user.position}, 직책={user.role}")
        
        # 담당자들의 부서/본부 정보 수집
        responsible_departments = set()
        responsible_headquarters = set()
        for user in responsible_users:
            if user.department:
                responsible_departments.add(user.department)
            if user.headquarters:
                responsible_headquarters.add(user.headquarters)
        
        print(f"\n담당자 부서: {responsible_departments}")
        print(f"담당자 본부: {responsible_headquarters}")
        
        # 모든 팀장 찾기
        print("\n[1] 모든 팀장 조회:")
        all_team_leaders = (
            db.query(User)
            .filter(
                ((User.position == "팀장") | (User.role == "팀장"))
                & User.email.isnot(None)
            )
            .all()
        )
        print(f"  전체 팀장 수: {len(all_team_leaders)}명")
        for tl in all_team_leaders:
            print(f"    {tl.name}: 부서={tl.department}, 본부={tl.headquarters}, 직위={tl.position}, 직책={tl.role}")
        
        # 담당자와 같은 부서/본부의 팀장 필터링
        print("\n[2] 담당자와 같은 부서/본부의 팀장 필터링:")
        if responsible_departments or responsible_headquarters:
            filtered_team_leaders = []
            for tl in all_team_leaders:
                match_dept = tl.department and tl.department in responsible_departments
                match_hq = tl.headquarters and tl.headquarters in responsible_headquarters
                if match_dept or match_hq:
                    filtered_team_leaders.append(tl)
                    print(f"    매칭: {tl.name} (부서={tl.department}, 본부={tl.headquarters})")
            print(f"  필터링된 팀장 수: {len(filtered_team_leaders)}명")
        else:
            print("  담당자의 부서/본부 정보가 없어 필터링할 수 없습니다.")
            print("  모든 팀장을 참조자로 추가할까요?")
        
        # DX본부 본부장 찾기
        print("\n[3] DX본부 본부장 조회:")
        dx_directors = (
            db.query(User)
            .filter(
                ((User.position == "본부장") | (User.role == "본부장"))
                & ((User.headquarters.like("%DX%")) | (User.general_headquarters.like("%DX%")))
                & User.email.isnot(None)
            )
            .all()
        )
        print(f"  DX본부 본부장 수: {len(dx_directors)}명")
        for director in dx_directors:
            print(f"    {director.name}: 본부={director.headquarters}, 총괄본부={director.general_headquarters}, 직위={director.position}, 직책={director.role}")
        
        # 모든 본부장 찾기 (DX 포함 여부 확인)
        print("\n[4] 모든 본부장 조회 (참고용):")
        all_directors = (
            db.query(User)
            .filter(
                ((User.position == "본부장") | (User.role == "본부장"))
                & User.email.isnot(None)
            )
            .all()
        )
        print(f"  전체 본부장 수: {len(all_directors)}명")
        for director in all_directors:
            print(f"    {director.name}: 본부={director.headquarters}, 총괄본부={director.general_headquarters}, 직위={director.position}, 직책={director.role}")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    debug_cc_recipients()

