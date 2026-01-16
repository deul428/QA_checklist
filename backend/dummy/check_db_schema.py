"""데이터베이스 스키마 확인 스크립트"""
import sys
from pathlib import Path
from sqlalchemy import text, inspect

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from services.database import engine

def check_schema():
    """실제 데이터베이스 스키마 확인"""
    print("=" * 60)
    print("데이터베이스 스키마 확인")
    print("=" * 60)
    
    inspector = inspect(engine)
    user_columns = inspector.get_columns('users')
    
    print("\nUser 테이블 컬럼:")
    print("-" * 60)
    for col in user_columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"  {col['name']}: {col['type']} {nullable}{default}")
    
    print("\n" + "=" * 60)
    print("모델에서 기대하는 컬럼:")
    print("-" * 60)
    expected_columns = [
        'id', 'employee_id', 'name', 'email', 'password_hash',
        'division', 'general_headquarters', 'headquarters',
        'department', 'position', 'role',
        'created_at', 'updated_at'
    ]
    for col in expected_columns:
        print(f"  {col}")
    
    print("\n" + "=" * 60)
    print("차이점 분석:")
    print("-" * 60)
    
    actual_column_names = {col['name'] for col in user_columns}
    expected_column_names = set(expected_columns)
    
    missing_in_db = expected_column_names - actual_column_names
    extra_in_db = actual_column_names - expected_column_names
    
    if missing_in_db:
        print(f"\nDB에 없는 컬럼 (모델에는 있음):")
        for col in missing_in_db:
            print(f"  - {col}")
    
    if extra_in_db:
        print(f"\nDB에만 있는 컬럼 (모델에는 없음):")
        for col in extra_in_db:
            print(f"  - {col}")
    
    if not missing_in_db and not extra_in_db:
        print("\n모든 컬럼이 일치합니다!")

if __name__ == "__main__":
    check_schema()

