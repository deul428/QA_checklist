"""
check_items 테이블에 environment 컬럼 추가 및 기존 데이터 마이그레이션 스크립트

1. check_items 테이블에 environment 컬럼 추가
2. 기존 항목들을 시스템이 지원하는 환경별로 복제
3. checklist_records, user_system_assignments, checklist_records_logs의 item_id 참조 업데이트
"""
import sys
import os
from pathlib import Path
import sqlite3

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
from models.models import CheckItem, System, ChecklistRecord, UserSystemAssignment, ChecklistRecordLog

def migrate_add_environment_to_check_items():
    """check_items에 environment 추가 및 데이터 마이그레이션"""
    db = SessionLocal()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("check_items에 environment 추가 마이그레이션 시작")
        print("=" * 60)
        print()
        
        # 1. environment 컬럼 추가
        print("1. environment 컬럼 추가 중...")
        try:
            cursor.execute(
                """
                ALTER TABLE check_items 
                ADD COLUMN environment VARCHAR(10) NOT NULL DEFAULT 'prd'
                """
            )
            print("  [OK] environment 컬럼 추가 완료")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  [INFO] environment 컬럼이 이미 존재합니다. 건너뜁니다.")
            else:
                raise
        
        # 2. 기존 UniqueConstraint 삭제 (나중에 다시 생성)
        print("\n2. 기존 UniqueConstraint 삭제 중...")
        try:
            # SQLite는 직접 제약조건 삭제가 어려우므로, 새 테이블을 만들어서 데이터 복사하는 방식 사용
            # 하지만 더 간단한 방법: 기존 데이터를 먼저 처리한 후 제약조건 재생성
            print("  [INFO] SQLite는 ALTER TABLE로 제약조건을 직접 삭제할 수 없습니다.")
            print("  [INFO] 데이터 마이그레이션 후 모델에서 제약조건이 자동으로 적용됩니다.")
        except Exception as e:
                print(f"  [INFO] 제약조건 삭제 중 오류 (무시 가능): {e}")
        
        conn.commit()
        
        # 3. 기존 항목들을 환경별로 복제
        print("\n3. 기존 항목을 환경별로 복제 중...")
        systems = {s.system_id: s for s in db.query(System).all()}
        
        # (system_id, item_name) 조합으로 그룹화하여 처리
        # 이미 환경별로 항목이 존재하는 경우를 올바르게 처리
        item_groups = db.execute(
            text("""
                SELECT DISTINCT system_id, item_name
                FROM check_items
                WHERE status = 'active'
            """)
        ).fetchall()
        
        item_mapping = {}  # {(system_id, item_name): {env: item_id}}
        total_created = 0
        
        for system_id, item_name in item_groups:
            system = systems.get(system_id)
            if not system:
                print(f"  [WARN] 시스템 ID {system_id}를 찾을 수 없습니다. 건너뜁니다.")
                continue
            
            # 시스템이 지원하는 환경 목록
            supported_environments = []
            if system.has_dev:
                supported_environments.append("dev")
            if system.has_stg:
                supported_environments.append("stg")
            if system.has_prd:
                supported_environments.append("prd")
            
            if not supported_environments:
                print(f"  [WARN] 시스템 ID {system_id}가 지원하는 환경이 없습니다. 건너뜁니다.")
                continue
            
            key = (system_id, item_name)
            item_mapping[key] = {}
            
            # 각 환경별로 항목 확인 및 생성
            for env in supported_environments:
                # 이미 해당 환경에 항목이 존재하는지 확인
                existing = db.execute(
                    text("""
                        SELECT item_id 
                        FROM check_items 
                        WHERE system_id = :system_id 
                        AND item_name = :item_name 
                        AND environment = :env
                        AND status = 'active'
                    """),
                    {"system_id": system_id, "item_name": item_name, "env": env}
                ).first()
                
                if existing:
                    # 이미 존재하면 그대로 사용
                    item_mapping[key][env] = existing[0]
                    print(f"  [OK] system_id={system_id}, item_name={item_name}, env={env}: item_id={existing[0]} (이미 존재)")
                else:
                    # 새 항목 생성 (기존 항목 중 하나를 참조하여 복제)
                    # 같은 system_id와 item_name을 가진 항목 중 하나를 찾아서 복제
                    source_item = db.execute(
                        text("""
                            SELECT item_id, item_description, status, created_at
                            FROM check_items
                            WHERE system_id = :system_id 
                            AND item_name = :item_name
                            AND status = 'active'
                            LIMIT 1
                        """),
                        {"system_id": system_id, "item_name": item_name}
                    ).first()
                    
                    if source_item:
                        new_item_id = db.execute(
                            text("""
                                INSERT INTO check_items (system_id, item_name, item_description, status, created_at, environment)
                                VALUES (:system_id, :item_name, :item_description, :status, :created_at, :env)
                            """),
                            {
                                "system_id": system_id,
                                "item_name": item_name,
                                "item_description": source_item[1],
                                "status": source_item[2],
                                "created_at": source_item[3],
                                "env": env
                            }
                        ).lastrowid
                        item_mapping[key][env] = new_item_id
                        total_created += 1
                        print(f"  ✓ system_id={system_id}, item_name={item_name}, env={env}: 새 항목 생성 (item_id={new_item_id})")
                    else:
                        print(f"  [WARN] system_id={system_id}, item_name={item_name}: 복제할 소스 항목을 찾을 수 없습니다.")
        
        db.commit()
        print(f"\n  총 {total_created}개의 새 항목이 생성되었습니다.")
        
        # 4. checklist_records의 item_id 참조 업데이트
        print("\n4. checklist_records의 item_id 참조 업데이트 중...")
        total_records_updated = 0
        
        # 모든 checklist_records를 조회하여 올바른 item_id로 업데이트
        all_records = db.query(ChecklistRecord).all()
        for record in all_records:
            # record의 item_id로 check_items에서 system_id와 item_name 찾기
            item = db.query(CheckItem).filter(CheckItem.item_id == record.check_item_id).first()
            if item:
                key = (item.system_id, item.item_name)
                env_mapping = item_mapping.get(key, {})
                # record의 environment에 맞는 새 item_id 찾기
                new_item_id = env_mapping.get(record.environment)
                if new_item_id and new_item_id != record.check_item_id:
                    record.check_item_id = new_item_id
                    total_records_updated += 1
        
        db.commit()
        print(f"  ✓ {total_records_updated}개의 checklist_records 업데이트 완료")
        
        # 5. user_system_assignments의 item_id 참조 업데이트
        print("\n5. user_system_assignments의 item_id 참조 업데이트 중...")
        total_assignments_updated = 0
        
        # 모든 user_system_assignments를 조회하여 올바른 item_id로 업데이트
        all_assignments = db.query(UserSystemAssignment).all()
        for assignment in all_assignments:
            # assignment의 item_id로 check_items에서 system_id와 item_name 찾기
            item = db.query(CheckItem).filter(CheckItem.item_id == assignment.item_id).first()
            if item:
                key = (item.system_id, item.item_name)
                env_mapping = item_mapping.get(key, {})
                # assignment는 환경 무관하므로, 모든 환경의 item_id 중 하나를 사용
                # 우선순위: prd > stg > dev
                new_item_id = None
                for env in ['prd', 'stg', 'dev']:
                    if env in env_mapping:
                        new_item_id = env_mapping[env]
                        break
                if new_item_id and new_item_id != assignment.item_id:
                    assignment.item_id = new_item_id
                    total_assignments_updated += 1
        
        db.commit()
        print(f"  ✓ {total_assignments_updated}개의 user_system_assignments 업데이트 완료")
        
        # 6. checklist_records_logs의 item_id 참조 업데이트
        print("\n6. checklist_records_logs의 item_id 참조 업데이트 중...")
        total_logs_updated = 0
        
        # 모든 checklist_records_logs를 조회하여 올바른 item_id로 업데이트
        all_logs = db.query(ChecklistRecordLog).all()
        for log in all_logs:
            # log의 check_item_id로 check_items에서 system_id와 item_name 찾기
            item = db.query(CheckItem).filter(CheckItem.item_id == log.check_item_id).first()
            if item:
                key = (item.system_id, item.item_name)
                env_mapping = item_mapping.get(key, {})
                # log의 environment에 맞는 새 item_id 찾기
                new_item_id = env_mapping.get(log.environment)
                if new_item_id and new_item_id != log.check_item_id:
                    log.check_item_id = new_item_id
                    total_logs_updated += 1
        
        db.commit()
        print(f"  ✓ {total_logs_updated}개의 checklist_records_logs 업데이트 완료")
        
        print("\n" + "=" * 60)
        print("마이그레이션 완료!")
        print("=" * 60)
        print(f"  - 새로 생성된 항목: {total_created}개")
        print(f"  - checklist_records 업데이트: {total_records_updated}개")
        print(f"  - user_system_assignments 업데이트: {total_assignments_updated}개")
        print(f"  - checklist_records_logs 업데이트: {total_logs_updated}개")
        
        # 확인: 컬럼이 제대로 추가되었는지 확인
        cursor.execute("PRAGMA table_info(check_items)")
        columns = cursor.fetchall()
        print("\n[확인] check_items 테이블 컬럼 목록:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) - nullable: {not col[3]}")
        
    except Exception as e:
        conn.rollback()
        db.rollback()
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        conn.close()
        db.close()

if __name__ == "__main__":
    migrate_add_environment_to_check_items()

