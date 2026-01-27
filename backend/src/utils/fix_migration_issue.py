"""
마이그레이션 문제 수정 스크립트

문제: 마이그레이션 스크립트가 이미 환경별로 항목이 존재하는 경우를 제대로 처리하지 못함
해결: 이미 환경별로 항목이 존재하는 경우, 기존 항목을 유지하고 checklist_records의 item_id를 올바르게 매핑
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

# 데이터베이스 파일 경로 확인
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
    print(f"데이터베이스 파일을 찾을 수 없습니다.")
    exit(1)

print(f"데이터베이스 경로: {db_path}")
print("=" * 60)

# SQLAlchemy를 사용하여 데이터 조회
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session
from services.database import SessionLocal
from models.models import CheckItem, System, ChecklistRecord, ChecklistRecordLog

def fix_migration_issue():
    """마이그레이션 문제 수정"""
    db = SessionLocal()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("\n마이그레이션 문제 수정 시작")
        print("=" * 60)
        
        # 1. 현재 상태 확인
        print("\n1. 현재 상태 확인:")
        
        # checklist_records의 환경별 기록 수
        cursor.execute("""
            SELECT environment, COUNT(*) as count
            FROM checklist_records
            GROUP BY environment
        """)
        record_counts = cursor.fetchall()
        print("  checklist_records 환경별 기록:")
        for env, count in record_counts:
            print(f"    {env}: {count}개")
        
        # checklist_records_logs의 환경별 기록 수
        cursor.execute("""
            SELECT environment, COUNT(*) as count
            FROM checklist_records_logs
            GROUP BY environment
        """)
        log_counts = cursor.fetchall()
        print("  checklist_records_logs 환경별 기록:")
        for env, count in log_counts:
            print(f"    {env}: {count}개")
        
        # 2. checklist_records의 item_id가 올바른 check_items를 가리키는지 확인
        print("\n2. checklist_records의 item_id 매칭 확인:")
        cursor.execute("""
            SELECT 
                cr.records_id,
                cr.item_id,
                cr.environment,
                cr.check_date,
                ci.item_id as check_item_id,
                ci.environment as check_item_env
            FROM checklist_records cr
            LEFT JOIN check_items ci ON cr.item_id = ci.item_id
            ORDER BY cr.environment, cr.check_date
        """)
        records = cursor.fetchall()
        
        mismatched = []
        for record in records:
            records_id, item_id, env, check_date, check_item_id, check_item_env = record
            if check_item_id is None:
                mismatched.append((records_id, item_id, env, "항목이 존재하지 않음"))
            elif check_item_env != env:
                mismatched.append((records_id, item_id, env, f"환경 불일치: 항목은 {check_item_env}, 기록은 {env}"))
        
        if mismatched:
            print(f"  [WARN] {len(mismatched)}개의 기록이 매칭 문제가 있습니다:")
            for records_id, item_id, env, issue in mismatched[:10]:
                print(f"    records_id={records_id}, item_id={item_id}, env={env}: {issue}")
            if len(mismatched) > 10:
                print(f"    ... (총 {len(mismatched)}개 중 10개만 표시)")
        else:
            print("  [OK] 모든 기록이 올바르게 매칭됩니다.")
        
        # 3. checklist_records_logs의 check_item_id가 올바른 check_items를 가리키는지 확인
        print("\n3. checklist_records_logs의 check_item_id 매칭 확인:")
        cursor.execute("""
            SELECT 
                log.id,
                log.check_item_id,
                log.environment,
                log.check_date,
                ci.item_id as check_item_id_match,
                ci.environment as check_item_env
            FROM checklist_records_logs log
            LEFT JOIN check_items ci ON log.check_item_id = ci.item_id
            ORDER BY log.environment, log.check_date
        """)
        logs = cursor.fetchall()
        
        mismatched_logs = []
        for log in logs:
            log_id, check_item_id, env, check_date, check_item_id_match, check_item_env = log
            if check_item_id_match is None:
                mismatched_logs.append((log_id, check_item_id, env, "항목이 존재하지 않음"))
            elif check_item_env != env:
                mismatched_logs.append((log_id, check_item_id, env, f"환경 불일치: 항목은 {check_item_env}, 로그는 {env}"))
        
        if mismatched_logs:
            print(f"  [WARN] {len(mismatched_logs)}개의 로그가 매칭 문제가 있습니다:")
            for log_id, check_item_id, env, issue in mismatched_logs[:10]:
                print(f"    log_id={log_id}, check_item_id={check_item_id}, env={env}: {issue}")
            if len(mismatched_logs) > 10:
                print(f"    ... (총 {len(mismatched_logs)}개 중 10개만 표시)")
        else:
            print("  [OK] 모든 로그가 올바르게 매칭됩니다.")
        
        # 4. 환경 불일치 문제 수정
        print("\n4. 환경 불일치 문제 수정:")
        
        # checklist_records 수정
        fixed_records = 0
        for records_id, item_id, env, issue in mismatched:
            if "환경 불일치" in issue:
                # 올바른 item_id 찾기
                cursor.execute("""
                    SELECT item_id
                    FROM check_items
                    WHERE system_id = (
                        SELECT system_id FROM checklist_records WHERE records_id = ?
                    )
                    AND item_name = (
                        SELECT item_name FROM check_items WHERE item_id = (
                            SELECT item_id FROM checklist_records WHERE records_id = ?
                        )
                    )
                    AND environment = ?
                """, (records_id, records_id, env))
                result = cursor.fetchone()
                if result:
                    new_item_id = result[0]
                    cursor.execute("""
                        UPDATE checklist_records
                        SET item_id = ?
                        WHERE records_id = ?
                    """, (new_item_id, records_id))
                    fixed_records += 1
                    print(f"  [FIX] records_id={records_id}: item_id {item_id} -> {new_item_id} (env: {env})")
        
        # checklist_records_logs 수정
        fixed_logs = 0
        for log_id, check_item_id, env, issue in mismatched_logs:
            if "환경 불일치" in issue:
                # 올바른 item_id 찾기
                cursor.execute("""
                    SELECT item_id
                    FROM check_items
                    WHERE system_id = (
                        SELECT system_id FROM checklist_records_logs WHERE id = ?
                    )
                    AND item_name = (
                        SELECT item_name FROM check_items WHERE item_id = (
                            SELECT check_item_id FROM checklist_records_logs WHERE id = ?
                        )
                    )
                    AND environment = ?
                """, (log_id, log_id, env))
                result = cursor.fetchone()
                if result:
                    new_item_id = result[0]
                    cursor.execute("""
                        UPDATE checklist_records_logs
                        SET check_item_id = ?
                        WHERE id = ?
                    """, (new_item_id, log_id))
                    fixed_logs += 1
                    print(f"  [FIX] log_id={log_id}: check_item_id {check_item_id} -> {new_item_id} (env: {env})")
        
        conn.commit()
        print(f"\n  수정 완료: checklist_records {fixed_records}개, checklist_records_logs {fixed_logs}개")
        
        print("\n" + "=" * 60)
        print("수정 완료!")
        print("=" * 60)
        
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
    fix_migration_issue()

