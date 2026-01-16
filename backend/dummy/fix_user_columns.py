"""User 테이블 컬럼 이름 수정 스크립트"""
import sys
from pathlib import Path
from sqlalchemy import text

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import engine

def fix_column_names():
    """컬럼 이름을 모델에 맞게 수정"""
    print("=" * 60)
    print("User 테이블 컬럼 이름 수정")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # SQLite는 ALTER TABLE RENAME COLUMN을 지원합니다 (SQLite 3.25.0+)
            # 하지만 안전하게 하기 위해 먼저 컬럼 존재 여부 확인
            
            # 1. sector -> division
            print("\n[1] sector -> division 변경")
            try:
                conn.execute(text("ALTER TABLE users RENAME COLUMN sector TO division"))
                conn.commit()
                print("  성공: sector가 division으로 변경되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            # 2. high_headquarters -> general_headquarters
            print("\n[2] high_headquarters -> general_headquarters 변경")
            try:
                conn.execute(text("ALTER TABLE users RENAME COLUMN high_headquarters TO general_headquarters"))
                conn.commit()
                print("  성공: high_headquarters가 general_headquarters로 변경되었습니다.")
            except Exception as e:
                print(f"  오류: {e}")
                conn.rollback()
            
            print("\n" + "=" * 60)
            print("컬럼 이름 수정 완료")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_column_names()

