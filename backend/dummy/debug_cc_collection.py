"""참조자 수집 디버깅 스크립트"""
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

def debug_cc_collection():
    """참조자 수집 로직 디버깅"""
    db: Session = SessionLocal()
    
    try:
        print("="*60)
        print("참조자 수집 디버깅")
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
            print(f"  {user.name} ({user.employee_id}): 총괄본부={user.general_headquarters}, 부서={user.department}, 직위={user.position}, 직책={user.role}")
        
        # 수신인 정보
        recipient_emails = [user.email for user in responsible_users if user.email]
        recipient_names = [user.name for user in responsible_users if user.email]
        print(f"\n수신인: {len(recipient_emails)}명")
        print(f"  {', '.join(recipient_names)}")
        
        # 담당자들의 총괄본부 정보 수집
        responsible_general_headquarters = set()
        for user in responsible_users:
            if user.general_headquarters:
                responsible_general_headquarters.add(user.general_headquarters)
        
        print(f"\n담당자 총괄본부: {responsible_general_headquarters}")
        
        # 팀장 찾기
        print("\n[1] 팀장 조회:")
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
            print(f"    {tl.name}: 총괄본부={tl.general_headquarters}, 직위={tl.position}, 직책={tl.role}, 이메일={tl.email}")
        
        # 담당자와 같은 general_headquarters를 가진 팀장 필터링
        if responsible_general_headquarters:
            filtered_team_leaders = []
            for tl in all_team_leaders:
                if tl.general_headquarters and tl.general_headquarters in responsible_general_headquarters:
                    filtered_team_leaders.append(tl)
                    print(f"    [매칭] {tl.name} (총괄본부={tl.general_headquarters})")
            team_leaders = filtered_team_leaders
            print(f"  필터링된 팀장 수: {len(team_leaders)}명")
        else:
            print("  담당자의 총괄본부 정보가 없어 모든 팀장을 포함합니다.")
            team_leaders = all_team_leaders
        
        # DX본부 본부장 찾기
        print("\n[2] DX본부 본부장 조회:")
        dx_directors = (
            db.query(User)
            .filter(
                ((User.position == "본부장") | (User.role == "본부장"))
                & (User.division.like("%DX%"))
                & User.email.isnot(None)
            )
            .all()
        )
        print(f"  DX본부 본부장 수: {len(dx_directors)}명")
        for director in dx_directors:
            print(f"    {director.name}: division={director.division}, 직위={director.position}, 직책={director.role}, 이메일={director.email}")
        
        # CC 이메일 수집
        cc_email_dict = {}
        for tl in team_leaders:
            if tl.email and tl.email not in recipient_emails:
                cc_email_dict[tl.email] = tl.name
                print(f"    [팀장 추가] {tl.name} ({tl.email})")
        for director in dx_directors:
            if director.email and director.email not in recipient_emails:
                cc_email_dict[director.email] = director.name
                print(f"    [본부장 추가] {director.name} ({director.email})")
        
        cc_emails = list(cc_email_dict.keys())
        cc_names = [cc_email_dict[email] for email in cc_emails]
        
        print(f"\n최종 참조자: {len(cc_emails)}명")
        if cc_names:
            print(f"  {', '.join(cc_names)}")
        else:
            print("  참조자가 없습니다!")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    debug_cc_collection()

