"""CSV 파일의 실제 행 수 확인 스크립트"""
import csv
from pathlib import Path

csv_file = Path("database/checklist_data_0115_bom.csv")

print("="*60)
print("CSV 파일 분석")
print("="*60)

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    
    total_rows = 0
    valid_rows = 0
    skipped_rows = []
    
    for row_num, row in enumerate(reader, start=2):
        total_rows += 1
        user_name = row.get('user_name', '').strip()
        system_name = row.get('system_id', '').strip()
        item_name = row.get('item_name', '').strip()
        
        if not system_name or not item_name:
            skipped_rows.append((row_num, user_name, system_name, item_name))
        else:
            valid_rows += 1

print(f"\n총 CSV 행 수 (헤더 제외): {total_rows}")
print(f"유효한 행 수: {valid_rows}")
print(f"건너뛴 행 수: {len(skipped_rows)}")

if skipped_rows:
    print(f"\n건너뛴 행 목록:")
    for row_num, user_name, system_name, item_name in skipped_rows:
        print(f"  행 {row_num}: user={user_name}, system={system_name}, item={item_name}")

print("="*60)

