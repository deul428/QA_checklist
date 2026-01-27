"""
checklist_records_logs를 확인하여 손실된 데이터 확인
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

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # 1. checklist_records_logs의 환경별 기록 확인
    print("\n1. checklist_records_logs의 환경별 기록:")
    cursor.execute("""
        SELECT environment, COUNT(*) as count
        FROM checklist_records_logs
        GROUP BY environment
        ORDER BY environment
    """)
    log_env_counts = cursor.fetchall()
    for env, count in log_env_counts:
        print(f"    {env}: {count}개")
    
    # 2. checklist_records_logs 테이블 구조 확인
    print("\n2. checklist_records_logs 테이블 구조:")
    cursor.execute("PRAGMA table_info(checklist_records_logs)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"    {col[1]} ({col[2]})")
    
    # item_id 컬럼명 확인
    item_id_col = None
    for col in columns:
        if col[1] in ['item_id', 'check_item_id']:
            item_id_col = col[1]
            break
    
    if item_id_col:
        # checklist_records_logs에는 있지만 checklist_records에는 없는 기록 확인
        print(f"\n3. checklist_records_logs에는 있지만 checklist_records에는 없는 기록:")
        cursor.execute(f"""
            SELECT 
                log.environment,
                log.check_date,
                COUNT(*) as count
            FROM checklist_records_logs log
            LEFT JOIN checklist_records cr ON 
                log.{item_id_col} = cr.item_id AND 
                log.check_date = cr.check_date AND 
                log.environment = cr.environment
            WHERE cr.records_id IS NULL
            GROUP BY log.environment, log.check_date
            ORDER BY log.environment, log.check_date
        """)
        missing_records = cursor.fetchall()
        if missing_records:
            print("    [WARN] 다음 기록들이 로그에는 있지만 실제 기록에는 없습니다:")
            for env, check_date, count in missing_records:
                print(f"        {env}, {check_date}: {count}개")
        else:
            print("    [OK] 모든 로그가 실제 기록과 일치합니다.")
        
        # 각 환경별로 최근 로그 확인
        print(f"\n4. 각 환경별 최근 로그 (최대 10개):")
        for env in ['dev', 'stg', 'prd']:
            cursor.execute(f"""
                SELECT 
                    id,
                    {item_id_col},
                    check_date,
                    environment,
                    status,
                    action,
                    created_at
                FROM checklist_records_logs
                WHERE environment = ?
                ORDER BY created_at DESC
                LIMIT 10
            """, (env,))
            logs = cursor.fetchall()
            print(f"\n    {env} 환경:")
            if logs:
                for log in logs:
                    print(f"        id={log[0]}, {item_id_col}={log[1]}, date={log[2]}, status={log[4]}, action={log[5]}, created_at={log[6]}")
            else:
                print("        (기록 없음)")
        
        # checklist_records_logs의 item_id가 check_items에 존재하는지 확인
        print(f"\n5. checklist_records_logs의 {item_id_col} 매칭 확인:")
        cursor.execute(f"""
            SELECT 
                log.environment,
                COUNT(DISTINCT log.{item_id_col}) as unique_item_ids_in_logs,
                COUNT(DISTINCT ci.item_id) as unique_item_ids_in_items
            FROM checklist_records_logs log
            LEFT JOIN check_items ci ON log.{item_id_col} = ci.item_id AND log.environment = ci.environment
            GROUP BY log.environment
        """)
        matching = cursor.fetchall()
        for env, logs_count, items_count in matching:
            print(f"    {env}: logs의 {item_id_col}={logs_count}개, items의 item_id={items_count}개 매칭")
        
        # 매칭되지 않는 로그 확인
        print(f"\n6. 매칭되지 않는 checklist_records_logs 확인:")
        cursor.execute(f"""
            SELECT 
                log.environment,
                COUNT(*) as count
            FROM checklist_records_logs log
            LEFT JOIN check_items ci ON log.{item_id_col} = ci.item_id AND log.environment = ci.environment
            WHERE ci.item_id IS NULL
            GROUP BY log.environment
        """)
        unmatched = cursor.fetchall()
        if unmatched:
            print("    [WARN] 다음 로그들이 매칭되는 항목이 없습니다:")
            for env, count in unmatched:
                print(f"        {env}: {count}개")
        else:
            print("    [OK] 모든 로그가 매칭되는 항목을 가지고 있습니다.")
    else:
        print("\n3. item_id 컬럼을 찾을 수 없습니다.")

except Exception as e:
    print(f"\n[ERROR] 오류 발생: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

