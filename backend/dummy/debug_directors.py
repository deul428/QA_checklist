"""본부장 조회 디버깅 스크립트"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import User

def debug_directors():
    """본부장 조회 디버깅"""
    db: Session = SessionLocal()
    
    try:
        print("="*60)
        print("본부장 조회 디버깅")
        print("="*60)
        
        # 모든 본부장 조회
        print("\n[1] 모든 본부장 조회:")
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
            print(f"    {director.name}: division={director.division}, 직위={director.position}, 직책={director.role}, 이메일={director.email}")
        
        # DX본부 본부장 조회 (division에 DX 포함)
        print("\n[2] DX본부 본부장 조회 (division LIKE '%DX%'):")
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
        
        # division에 DX가 포함되지 않은 본부장들
        print("\n[3] division에 DX가 포함되지 않은 본부장:")
        non_dx_directors = [
            d for d in all_directors 
            if not d.division or "DX" not in d.division
        ]
        print(f"  수: {len(non_dx_directors)}명")
        for director in non_dx_directors:
            print(f"    {director.name}: division={director.division}")
        
        # division이 None인 본부장들
        print("\n[4] division이 None인 본부장:")
        none_division_directors = [
            d for d in all_directors 
            if d.division is None
        ]
        print(f"  수: {len(none_division_directors)}명")
        for director in none_division_directors:
            print(f"    {director.name}: division={director.division}")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    debug_directors()

