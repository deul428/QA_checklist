"""
user_system_assignments 테이블에서 environment 컬럼 제거 및 중복 배정 통합 마이그레이션 스크립트

1. user_system_assignments에서 중복 배정 통합 (prd > dev > stg 우선순위)
2. environment 컬럼 제거
3. UniqueConstraint 재생성
"""
import sys
import os
from pathlib import Path
import sqlite3
from collections import defaultdict

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent.parent.parent

# 데이터베이스 파일 경로 확인 (여러 가능한 위치 시도)
possible_db_paths = [
    project_root / "database" / "checklist.db",
    project_root / "database" / "qa_checklist.db",
    project_root / "qa_checklist.db",
]

db_path = None
for path in possible_db_paths:
    if path.exists():
        db_path = path
        break

if not db_path:
    print(f"데이터베이스 파일을 찾을 수 없습니다. 다음 경로를 확인했습니다:")
    for path in possible_db_paths:
        print(f"  - {path}")
    exit(1)

print(f"데이터베이스 경로: {db_path}")

# SQLAlchemy를 사용하여 데이터 조회
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import UserSystemAssignment

def migrate_remove_environment_from_assignments():
    """user_system_assignments에서 environment 제거 및 중복 배정 통합"""
    db = SessionLocal()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("user_system_assignments에서 environment 제거 마이그레이션 시작")
        print("=" * 60)
        print()
        
        # 1. 중복 배정 통합 (prd > dev > stg 우선순위)
        print("1. 중복 배정 통합 중...")
        all_assignments = db.query(UserSystemAssignment).all()
        
        # 그룹화: (user_id, system_id, item_id) -> [assignments]
        assignment_groups = defaultdict(list)
        for assignment in all_assignments:
            key = (assignment.user_id, assignment.system_id, assignment.item_id)
            assignment_groups[key].append(assignment)
        
        # 여러 환경에 걸친 배정 그룹만 필터링
        groups_to_merge = {k: v for k, v in assignment_groups.items() if len(v) > 1}
        
        total_merged = 0
        total_deleted = 0
        
        # 환경 우선순위: prd > dev > stg
        env_priority = {"prd": 3, "dev": 2, "stg": 1}
        
        for key, assignments in groups_to_merge.items():
            # 우선순위에 따라 정렬 (높은 우선순위가 먼저)
            assignments_sorted = sorted(
                assignments,
                key=lambda a: env_priority.get(a.environment, 0),
                reverse=True
            )
            
            # 첫 번째 배정 유지 (가장 높은 우선순위)
            primary_assignment = assignments_sorted[0]
            
            # 나머지 배정 삭제
            for assignment in assignments_sorted[1:]:
                db.delete(assignment)
                total_deleted += 1
            
            total_merged += len(assignments) - 1
        
        db.commit()
        print(f"  [OK] {total_merged}개 그룹에서 {total_deleted}개의 중복 배정이 삭제되었습니다.")
        
        # 2. 기존 UniqueConstraint 삭제 (SQLite는 직접 삭제 불가, 새 테이블 생성 방식 사용)
        print("\n2. UniqueConstraint 재생성 준비 중...")
        print("  [INFO] SQLite는 ALTER TABLE로 제약조건을 직접 삭제할 수 없습니다.")
        print("  [INFO] environment 컬럼 제거 후 모델에서 제약조건이 자동으로 적용됩니다.")
        
        # 3. environment 컬럼 제거
        print("\n3. environment 컬럼 제거 중...")
        try:
            # 뷰가 테이블을 참조하고 있을 수 있으므로 먼저 뷰 삭제
            print("  [INFO] 뷰 확인 및 삭제 중...")
            # user_system_assignments를 참조하는 뷰 찾기
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND sql LIKE '%user_system_assignments%'")
            views = cursor.fetchall()
            view_names = [v[0] for v in views]
            
            # checklist_records_view도 확인 (checklist_records 테이블 변경 시 영향을 받을 수 있음)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='checklist_records_view'")
            checklist_views = cursor.fetchall()
            checklist_view_names = [v[0] for v in checklist_views]
            view_names.extend(checklist_view_names)
            
            for view_name in view_names:
                try:
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    print(f"  [INFO] 뷰 '{view_name}' 삭제됨")
                except Exception as e:
                    print(f"  [WARN] 뷰 '{view_name}' 삭제 실패 (무시): {e}")
            
            # 기존 임시 테이블이 있으면 삭제
            cursor.execute("DROP TABLE IF EXISTS user_system_assignments_new")
            
            # SQLite는 컬럼 삭제를 직접 지원하지 않으므로, 새 테이블을 만들어서 데이터 복사
            cursor.execute("""
                CREATE TABLE user_system_assignments_new (
                    assign_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(50) NOT NULL,
                    system_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (system_id) REFERENCES systems(system_id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES check_items(item_id) ON DELETE CASCADE,
                    UNIQUE(user_id, system_id, item_id)
                )
            """)
            
            # 데이터 복사
            cursor.execute("""
                INSERT INTO user_system_assignments_new (assign_id, user_id, system_id, item_id, created_at)
                SELECT assign_id, user_id, system_id, item_id, created_at
                FROM user_system_assignments
            """)
            
            # 기존 테이블 삭제
            cursor.execute("DROP TABLE user_system_assignments")
            
            # 새 테이블 이름 변경
            cursor.execute("ALTER TABLE user_system_assignments_new RENAME TO user_system_assignments")
            
            conn.commit()
            print("  [OK] environment 컬럼 제거 완료")
            if view_names:
                print(f"  [INFO] 삭제된 뷰를 수동으로 재생성해야 할 수 있습니다: {', '.join(view_names)}")
        except sqlite3.OperationalError as e:
            print(f"  [ERROR] 오류 발생: {e}")
            conn.rollback()
            raise
        
        # 4. 인덱스 확인
        print("\n4. 인덱스 확인 중...")
        cursor.execute("PRAGMA index_list('user_system_assignments')")
        indexes = cursor.fetchall()
        print(f"  [INFO] 현재 인덱스 수: {len(indexes)}")
        
        # 5. 최종 확인
        print("\n" + "=" * 60)
        print("마이그레이션 완료!")
        print("=" * 60)
        print(f"  - 통합된 배정 그룹: {total_merged}개")
        print(f"  - 삭제된 중복 배정: {total_deleted}개")
        
        # 확인: 컬럼이 제대로 제거되었는지 확인
        cursor.execute("PRAGMA table_info(user_system_assignments)")
        columns = cursor.fetchall()
        print("\n[확인] user_system_assignments 테이블 컬럼 목록:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) - nullable: {not col[3]}")
        
        # environment 컬럼이 여전히 있는지 확인
        column_names = [col[1] for col in columns]
        if "environment" in column_names:
            print("\n  [WARN] environment 컬럼이 여전히 존재합니다!")
        else:
            print("\n  [OK] environment 컬럼이 성공적으로 제거되었습니다.")
        
    except Exception as e:
        conn.rollback()
        db.rollback()
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        conn.close()
        db.close()

if __name__ == "__main__":
    migrate_remove_environment_from_assignments()

