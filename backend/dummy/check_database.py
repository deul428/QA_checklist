"""데이터베이스 점검 스크립트"""
import sys
from pathlib import Path
from sqlalchemy import text, inspect

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import SessionLocal, engine
from models.models import User, System, CheckItem, UserSystemAssignment, ChecklistRecord

def check_database():
    """데이터베이스 전체 점검"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("데이터베이스 점검 시작")
        print("=" * 60)
        
        # 1. User 테이블 스키마 확인
        print("\n[1] User 테이블 스키마 확인")
        print("-" * 60)
        inspector = inspect(engine)
        user_columns = inspector.get_columns('users')
        print("컬럼 목록:")
        for col in user_columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default}")
        
        # 2. User 테이블 데이터 통계
        print("\n[2] User 테이블 데이터 통계")
        print("-" * 60)
        total_users = db.query(User).count()
        print(f"총 사용자 수: {total_users}")
        
        # 필수 필드 누락 확인
        missing_employee_id = db.query(User).filter(User.employee_id == None).count()
        missing_name = db.query(User).filter(User.name == None).count()
        missing_email = db.query(User).filter(User.email == None).count()
        missing_password = db.query(User).filter(User.password_hash == None).count()
        
        print(f"\n필수 필드 누락:")
        print(f"  - employee_id 누락: {missing_employee_id}명")
        print(f"  - name 누락: {missing_name}명")
        print(f"  - email 누락: {missing_email}명")
        print(f"  - password_hash 누락: {missing_password}명")
        
        # 중복 employee_id 확인
        print(f"\n중복 확인:")
        duplicate_query = db.execute(text("""
            SELECT employee_id, COUNT(*) as cnt 
            FROM users 
            GROUP BY employee_id 
            HAVING COUNT(*) > 1
        """))
        duplicates = duplicate_query.fetchall()
        if duplicates:
            print(f"  - 중복된 employee_id: {len(duplicates)}개")
            for dup in duplicates:
                print(f"    * {dup[0]}: {dup[1]}개")
        else:
            print(f"  - 중복된 employee_id 없음")
        
        # 빈 문자열 확인
        empty_employee_id = db.query(User).filter(User.employee_id == "").count()
        empty_name = db.query(User).filter(User.name == "").count()
        empty_email = db.query(User).filter(User.email == "").count()
        
        print(f"\n빈 문자열 확인:")
        print(f"  - employee_id 빈 문자열: {empty_employee_id}개")
        print(f"  - name 빈 문자열: {empty_name}개")
        print(f"  - email 빈 문자열: {empty_email}개")
        
        # 3. 샘플 데이터 확인
        print("\n[3] 샘플 데이터 확인 (최대 5개)")
        print("-" * 60)
        sample_users = db.query(User).limit(5).all()
        for i, user in enumerate(sample_users, 1):
            print(f"\n사용자 {i}:")
            print(f"  ID: {user.id}")
            print(f"  사원번호: {user.employee_id}")
            print(f"  이름: {user.name}")
            print(f"  이메일: {user.email}")
            print(f"  비밀번호 해시: {'있음' if user.password_hash else '없음'}")
            print(f"  부문: {user.division}")
            print(f"  총괄본부: {user.general_headquarters}")
            print(f"  본부: {user.headquarters}")
            print(f"  부서: {user.department}")
            print(f"  직위: {user.position}")
            print(f"  직책: {user.role}")
            print(f"  생성일: {user.created_at}")
            print(f"  수정일: {user.updated_at}")
        
        # 4. 외래키 관계 확인
        print("\n[4] 외래키 관계 확인")
        print("-" * 60)
        
        # UserSystemAssignment 확인
        assignments_count = db.query(UserSystemAssignment).count()
        orphaned_assignments = db.query(UserSystemAssignment).join(
            User, UserSystemAssignment.user_id == User.id, isouter=True
        ).filter(User.id == None).count()
        
        print(f"UserSystemAssignment:")
        print(f"  - 총 할당 수: {assignments_count}")
        print(f"  - 고아 레코드 (존재하지 않는 user_id): {orphaned_assignments}개")
        
        # ChecklistRecord 확인
        records_count = db.query(ChecklistRecord).count()
        orphaned_records = db.query(ChecklistRecord).join(
            User, ChecklistRecord.user_id == User.id, isouter=True
        ).filter(User.id == None).count()
        
        print(f"\nChecklistRecord:")
        print(f"  - 총 기록 수: {records_count}")
        print(f"  - 고아 레코드 (존재하지 않는 user_id): {orphaned_records}개")
        
        # 5. 데이터베이스 무결성 체크
        print("\n[5] 데이터베이스 무결성 체크")
        print("-" * 60)
        
        # NULL이면 안 되는 필드에 NULL이 있는지 확인
        issues = []
        
        if missing_employee_id > 0:
            issues.append(f"employee_id가 NULL인 사용자 {missing_employee_id}명")
        if missing_name > 0:
            issues.append(f"name이 NULL인 사용자 {missing_name}명")
        if missing_email > 0:
            issues.append(f"email이 NULL인 사용자 {missing_email}명")
        if missing_password > 0:
            issues.append(f"password_hash가 NULL인 사용자 {missing_password}명")
        if empty_employee_id > 0:
            issues.append(f"employee_id가 빈 문자열인 사용자 {empty_employee_id}명")
        if empty_name > 0:
            issues.append(f"name이 빈 문자열인 사용자 {empty_name}명")
        if empty_email > 0:
            issues.append(f"email이 빈 문자열인 사용자 {empty_email}명")
        if duplicates:
            issues.append(f"중복된 employee_id {len(duplicates)}개")
        if orphaned_assignments > 0:
            issues.append(f"고아 UserSystemAssignment 레코드 {orphaned_assignments}개")
        if orphaned_records > 0:
            issues.append(f"고아 ChecklistRecord 레코드 {orphaned_records}개")
        
        if issues:
            print("⚠️ 발견된 문제:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ 문제 없음")
        
        print("\n" + "=" * 60)
        print("점검 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_database()

