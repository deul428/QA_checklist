"""
admin_logs 테이블에 environment 컬럼 추가 마이그레이션 스크립트

이 스크립트는 admin_logs 테이블에 environment 컬럼을 추가합니다.
- environment는 nullable=True (check_item의 경우는 NULL)
- CheckConstraint 추가: environment IN ('dev', 'stg', 'prd') OR environment IS NULL
"""

import sqlite3
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
project_root = Path(__file__).parent.parent.parent.parent
db_path = project_root / "database" / "checklist.db"

if not db_path.exists():
    print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
    exit(1)

print(f"데이터베이스 경로: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # 1. environment 컬럼 추가
    print("\n[1] environment 컬럼 추가 중...")
    try:
        cursor.execute(
            """
            ALTER TABLE admin_logs 
            ADD COLUMN environment VARCHAR(10) NULL
            """
        )
        print("  ✓ environment 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ⚠ environment 컬럼이 이미 존재합니다. 건너뜁니다.")
        else:
            raise

    # 2. CheckConstraint 추가 (SQLite는 ALTER TABLE로 제약조건 추가가 제한적이므로 스킵)
    # SQLite는 ALTER TABLE로 CHECK 제약조건을 직접 추가할 수 없습니다.
    # 모델에서 정의한 제약조건은 새 테이블 생성 시에만 적용됩니다.
    print("\n[2] CheckConstraint는 모델에서 정의되어 있습니다.")
    print("  ⚠ SQLite는 ALTER TABLE로 CHECK 제약조건을 추가할 수 없습니다.")
    print("  ✓ 모델의 CheckConstraint는 새 테이블 생성 시 자동으로 적용됩니다.")

    conn.commit()
    print("\n✅ 마이그레이션 완료!")

    # 확인: 컬럼이 제대로 추가되었는지 확인
    cursor.execute("PRAGMA table_info(admin_logs)")
    columns = cursor.fetchall()
    print("\n[확인] admin_logs 테이블 컬럼 목록:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]}) - nullable: {not col[3]}")

except Exception as e:
    conn.rollback()
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    conn.close()

