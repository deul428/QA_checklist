"""
user copy.csv 파일을 데이터베이스에 import하는 스크립트

사용법:
    python backend/src/utils/import_user_copy_csv.py
"""
import sys
import os
import csv
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import User
from services.auth import get_password_hash

# CSV 파일 경로
CSV_FILE = project_root / "database" / "user copy.csv"
DEFAULT_PASSWORD = "1234"  # 기본 비밀번호


def import_users():
    """CSV 파일에서 사용자 데이터를 읽어 데이터베이스에 import"""
    db: Session = SessionLocal()
    
    try:
        if not CSV_FILE.exists():
            print(f"오류: CSV 파일을 찾을 수 없습니다: {CSV_FILE}")
            return
        
        print(f"CSV 파일 읽기: {CSV_FILE}")
        
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            imported_count = 0
            updated_count = 0
            skipped_count = 0
            
            for row in reader:
                # 필수 필드 확인
                employee_id = row.get('사원번호', '').strip()
                name = row.get('사원명', '').strip()
                email = row.get('이메일', '').strip()
                
                if not employee_id or not name or not email:
                    print(f"  [건너뜀] 필수 필드 누락: 사원번호={employee_id}, 이름={name}, 이메일={email}")
                    skipped_count += 1
                    continue
                
                # 기존 사용자 확인
                existing_user = db.query(User).filter(User.employee_id == employee_id).first()
                
                # 조직 정보 필드 읽기
                division = row.get('부문', '').strip() or None
                general_headquarters = row.get('총괄본부', '').strip() or None
                headquarters = row.get('본부', '').strip() or None
                department = row.get('부서', '').strip() or None
                position = row.get('직위', '').strip() or None
                role = row.get('직책', '').strip() or None
                
                if existing_user:
                    # 기존 사용자 정보 업데이트
                    existing_user.name = name
                    existing_user.email = email
                    existing_user.division = division
                    existing_user.general_headquarters = general_headquarters
                    existing_user.headquarters = headquarters
                    existing_user.department = department
                    existing_user.position = position
                    existing_user.role = role
                    # 비밀번호는 업데이트하지 않음 (기존 비밀번호 유지)
                    print(f"  [업데이트] {name} ({employee_id}) - {email}")
                    updated_count += 1
                else:
                    # 새 사용자 생성
                    password_hash = get_password_hash(DEFAULT_PASSWORD)
                    new_user = User(
                        employee_id=employee_id,
                        name=name,
                        email=email,
                        password_hash=password_hash,
                        division=division,
                        general_headquarters=general_headquarters,
                        headquarters=headquarters,
                        department=department,
                        position=position,
                        role=role
                    )
                    db.add(new_user)
                    print(f"  [추가] {name} ({employee_id}) - {email}")
                    imported_count += 1
            
            db.commit()
            
            print("\n" + "="*50)
            print("Import 완료!")
            print(f"  새로 추가: {imported_count}명")
            print(f"  업데이트: {updated_count}명")
            print(f"  건너뜀: {skipped_count}명")
            print(f"  기본 비밀번호: {DEFAULT_PASSWORD}")
            print("="*50)
            
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import_users()

