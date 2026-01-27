"""
데이터베이스 상태 확인 스크립트
check_items와 checklist_records의 현재 상태를 확인합니다.
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
    # 1. check_items 테이블 상태 확인
    print("\n1. check_items 테이블 상태:")
    cursor.execute("""
        SELECT 
            system_id,
            item_name,
            environment,
            COUNT(*) as count,
            GROUP_CONCAT(item_id) as item_ids
        FROM check_items
        WHERE status = 'active'
        GROUP BY system_id, item_name, environment
        ORDER BY system_id, item_name, environment
    """)
    items = cursor.fetchall()
    
    print(f"  총 {len(items)}개의 고유한 (system_id, item_name, environment) 조합")
    for item in items[:20]:  # 처음 20개만 표시
        print(f"    system_id={item[0]}, item_name={item[1]}, environment={item[2]}, count={item[3]}, item_ids={item[4]}")
    if len(items) > 20:
        print(f"    ... (총 {len(items)}개 중 20개만 표시)")
    
    # 환경별 항목 수 확인
    cursor.execute("""
        SELECT environment, COUNT(*) as count
        FROM check_items
        WHERE status = 'active'
        GROUP BY environment
    """)
    env_counts = cursor.fetchall()
    print("\n  환경별 항목 수:")
    for env, count in env_counts:
        print(f"    {env}: {count}개")
    
    # 2. checklist_records 테이블 상태 확인
    print("\n2. checklist_records 테이블 상태:")
    cursor.execute("""
        SELECT environment, COUNT(*) as count
        FROM checklist_records
        GROUP BY environment
    """)
    record_env_counts = cursor.fetchall()
    print("  환경별 기록 수:")
    for env, count in record_env_counts:
        print(f"    {env}: {count}개")
    
    # 3. checklist_records 테이블 구조 확인
    print("\n3. checklist_records 테이블 구조:")
    cursor.execute("PRAGMA table_info(checklist_records)")
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
        print(f"\n4. check_items와 checklist_records의 {item_id_col} 매칭 확인:")
        cursor.execute(f"""
            SELECT 
                cr.environment,
                COUNT(DISTINCT cr.{item_id_col}) as unique_item_ids_in_records,
                COUNT(DISTINCT ci.item_id) as unique_item_ids_in_items
            FROM checklist_records cr
            LEFT JOIN check_items ci ON cr.{item_id_col} = ci.item_id AND cr.environment = ci.environment
            GROUP BY cr.environment
        """)
        matching = cursor.fetchall()
        for env, records_count, items_count in matching:
            print(f"    {env}: records의 {item_id_col}={records_count}개, items의 item_id={items_count}개 매칭")
        
        # 매칭되지 않는 checklist_records 확인
        print(f"\n5. 매칭되지 않는 checklist_records 확인:")
        cursor.execute(f"""
            SELECT 
                cr.environment,
                COUNT(*) as count
            FROM checklist_records cr
            LEFT JOIN check_items ci ON cr.{item_id_col} = ci.item_id AND cr.environment = ci.environment
            WHERE ci.item_id IS NULL
            GROUP BY cr.environment
        """)
        unmatched = cursor.fetchall()
        if unmatched:
            for env, count in unmatched:
                print(f"    [WARN] {env}: {count}개의 기록이 매칭되는 항목이 없습니다!")
        else:
            print("    [OK] 모든 기록이 매칭되는 항목을 가지고 있습니다.")
    else:
        print("\n4. item_id 컬럼을 찾을 수 없습니다.")
    
    # 5. 시스템별 환경 지원 확인
    print("\n5. 시스템별 환경 지원 확인:")
    cursor.execute("""
        SELECT 
            system_id,
            system_name,
            has_dev,
            has_stg,
            has_prd
        FROM systems
        ORDER BY system_id
    """)
    systems = cursor.fetchall()
    for sys_data in systems:
        print(f"    system_id={sys_data[0]}, name={sys_data[1]}, dev={sys_data[2]}, stg={sys_data[3]}, prd={sys_data[4]}")
    
    # 6. 각 시스템의 환경별 항목 수 확인
    print("\n6. 각 시스템의 환경별 항목 수:")
    cursor.execute("""
        SELECT 
            s.system_id,
            s.system_name,
            ci.environment,
            COUNT(*) as count
        FROM systems s
        LEFT JOIN check_items ci ON s.system_id = ci.system_id AND ci.status = 'active'
        GROUP BY s.system_id, s.system_name, ci.environment
        ORDER BY s.system_id, ci.environment
    """)
    system_env_counts = cursor.fetchall()
    for sys_id, sys_name, env, count in system_env_counts:
        if env:
            print(f"    system_id={sys_id}, name={sys_name}, {env}: {count}개")
    
except Exception as e:
    print(f"\n[ERROR] 오류 발생: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

