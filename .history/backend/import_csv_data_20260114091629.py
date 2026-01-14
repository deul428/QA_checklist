"""
CSV 파일을 데이터베이스에 임포트하는 스크립트
실행: python import_csv_data.py
"""
import csv
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, System, CheckItem, UserSystemAssignment, SpecialNote, ChecklistRecord
from auth import get_password_hash
import re

# 테이블 생성
Base.metadata.create_all(bind=engine)


def parse_week_info(week_str: str):
    """주차 정보 파싱 (예: '12월 3주차 월요일' -> date)"""
    match = re.search(r'(\d+)월\s*(\d+)주차', week_str)
    if match:
        month = int(match.group(1))
        week = int(match.group(2))
        # 월요일 = 0, 화요일 = 1, ..., 금요일 = 4
        if '월요일' in week_str:
            day_offset = 0
        elif '화요일' in week_str:
            day_offset = 1
        elif '수요일' in week_str:
            day_offset = 2
        elif '목요일' in week_str:
            day_offset = 3
        elif '금요일' in week_str:
            day_offset = 4
        else:
            day_offset = 0
        
        # 2024년 12월 3주차 월요일 계산 (12월 16일이 3주차 월요일로 가정)
        base_date = date(2024, 12, 16)  # 2024년 12월 16일 (월요일)
        target_date = base_date + timedelta(days=day_offset)
        return target_date
    return None


def normalize_status(status: str) -> str:
    """상태 정규화 (PASS, FAIL)"""
    status = status.strip().upper()
    if status in ['PASS', 'P', 'OK', 'O']:
        return 'PASS'
    elif status in ['FAIL', 'F', 'FAILED', 'NG', 'Fail']:
        return 'FAIL'
    return 'PASS'  # 기본값


def find_user_by_name(db: Session, name: str) -> User:
    """이름으로 실제 사용자 찾기 (user.csv에서 임포트된 사용자)"""
    # 이름에서 공백 제거 및 정규화
    name = name.strip()
    
    # 정확한 이름 매칭
    user = db.query(User).filter(User.name == name).first()
    if user:
        return user
    
    # 부분 매칭 시도 (예: "김민지B" -> "김민지B" 또는 "김민지")
    # 먼저 정확한 매칭을 시도하고, 없으면 부분 매칭
    return None


db: Session = SessionLocal()

try:
    # 기존 시스템/체크리스트 데이터만 삭제 (사용자는 유지)
    clear_existing = True
    
    if clear_existing:
        print("기존 시스템/체크리스트 데이터 삭제 중...")
        db.query(ChecklistRecord).delete()
        db.query(SpecialNote).delete()
        db.query(CheckItem).delete()
        db.query(UserSystemAssignment).delete()
        db.query(System).delete()
        # 사용자는 삭제하지 않음 (user.csv에서 이미 임포트됨)
        db.commit()
        print("기존 데이터 삭제 완료\n")
    
    # 기존 사용자 조회 (user.csv에서 임포트된 실제 사용자)
    print("기존 사용자 조회 중...")
    all_users = db.query(User).all()
    user_map = {}  # 이름 -> User 객체
    for user in all_users:
        user_map[user.name] = user
        # 이름의 변형도 매핑 (예: "김민지B"와 "김민지")
        if 'B' in user.name:
            base_name = user.name.replace('B', '').strip()
            if base_name not in user_map:
                user_map[base_name] = user
    
    print(f"기존 사용자 {len(all_users)}명 발견\n")
    
    # CSV 파일 읽기
    csv_file = 'example.csv'
    print(f"CSV 파일 읽기: {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        print("CSV 파일이 비어있습니다.")
        exit(1)
    
    # 헤더 파싱
    header = rows[0]
    print(f"헤더 컬럼 수: {len(header)}")
    
    # 컬럼 인덱스 찾기
    system_idx = 0  # 시스템
    item_idx = 1    # 항목
    special_note_idx = 2  # 특이사항
    checker_idx = 3  # 확인자
    
    # 주차별 날짜 컬럼 찾기
    date_columns = []
    checker_columns = []
    issue_column_idx = None
    
    for i, col in enumerate(header):
        col = col.strip()
        if '주차' in col and ('월요일' in col or '화요일' in col or '수요일' in col or '목요일' in col or '금요일' in col):
            date_columns.append((i, col))
            # 다음 컬럼이 확인자일 가능성
            if i + 1 < len(header) and header[i + 1].strip() == '확인자':
                checker_columns.append(i + 1)
        elif col == '이슈사항':
            issue_column_idx = i
    
    print(f"날짜 컬럼: {len(date_columns)}개")
    print(f"확인자 컬럼: {len(checker_columns)}개")
    
    # 시스템 및 체크 항목 생성
    print("\n시스템 및 체크 항목 생성 중...")
    systems_data = {}
    check_items_map = {}  # (system_name, item_name) -> CheckItem
    order_index = 1
    current_system = None
    current_item = None
    current_special_note = ""
    
    for row_idx, row in enumerate(rows[1:], 2):
        if len(row) < 4:
            continue
        
        system = row[system_idx].strip() if len(row) > system_idx and row[system_idx].strip() else None
        item = row[item_idx].strip() if len(row) > item_idx and row[item_idx].strip() else None
        special_note = row[special_note_idx].strip() if len(row) > special_note_idx and row[special_note_idx].strip() else None
        checker = row[checker_idx].strip() if len(row) > checker_idx and row[checker_idx].strip() else None
        
        # 시스템 업데이트
        if system:
            current_system = system
            if system not in systems_data:
                existing_system = db.query(System).filter(System.system_name == system).first()
                if existing_system:
                    systems_data[system] = existing_system
                else:
                    new_system = System(system_name=system)
                    db.add(new_system)
                    db.flush()
                    systems_data[system] = new_system
                    print(f"  새 시스템 생성: {system}")
        
        # 체크 항목 생성
        if item and current_system:
            current_item = item
            key = (current_system, current_item)
            
            if key not in check_items_map:
                system_obj = systems_data[current_system]
                existing_item = db.query(CheckItem).filter(
                    CheckItem.system_id == system_obj.id,
                    CheckItem.item_name == current_item
                ).first()
                
                if existing_item:
                    check_items_map[key] = existing_item
                else:
                    new_item = CheckItem(
                        system_id=system_obj.id,
                        item_name=current_item,
                        order_index=order_index
                    )
                    db.add(new_item)
                    db.flush()
                    check_items_map[key] = new_item
                    order_index += 1
            
            # 특이사항 처리
            if special_note:
                if current_special_note:
                    current_special_note += '\n' + special_note
                else:
                    current_special_note = special_note
            else:
                # 특이사항이 없으면 이전에 누적된 특이사항 저장
                if current_special_note and key in check_items_map:
                    check_item = check_items_map[key]
                    existing_note = db.query(SpecialNote).filter(
                        SpecialNote.check_item_id == check_item.id,
                        SpecialNote.note_text == current_special_note
                    ).first()
                    
                    if not existing_note:
                        note = SpecialNote(
                            check_item_id=check_item.id,
                            note_text=current_special_note,
                            is_active=True
                        )
                        db.add(note)
                    current_special_note = ""
        
        # 사용자-시스템 담당 관계 설정 (확인자 = 담당자)
        if checker and current_system:
            # 확인자 이름 파싱 (쉼표로 구분된 여러 이름)
            names = [name.strip() for name in checker.split(',') if name.strip()]
            system_obj = systems_data[current_system]
            
            for name in names:
                # 실제 사용자 찾기
                user = user_map.get(name)
                if not user:
                    # 부분 매칭 시도
                    for db_name, db_user in user_map.items():
                        if name in db_name or db_name in name:
                            user = db_user
                            break
                
                if user:
                    existing_assignment = db.query(UserSystemAssignment).filter(
                        UserSystemAssignment.user_id == user.id,
                        UserSystemAssignment.system_id == system_obj.id
                    ).first()
                    
                    if not existing_assignment:
                        assignment = UserSystemAssignment(
                            user_id=user.id,
                            system_id=system_obj.id
                        )
                        db.add(assignment)
                        print(f"  담당 관계 설정: {user.name} ({user.employee_id}) -> {system_obj.system_name}")
    
    db.commit()
    print(f"\n시스템 {len(systems_data)}개, 체크 항목 {len(check_items_map)}개 생성 완료\n")
    
    # 주차별 체크 기록 생성
    print("주차별 체크 기록 생성 중...")
    records_created = 0
    
    current_system = None
    current_item = None
    
    for row_idx, row in enumerate(rows[1:], 2):
        if len(row) < 4:
            continue
        
        system = row[system_idx].strip() if len(row) > system_idx and row[system_idx].strip() else None
        item = row[item_idx].strip() if len(row) > item_idx and row[item_idx].strip() else None
        
        if system:
            current_system = system
        if item:
            current_item = item
        
        if not current_system or not current_item:
            continue
        
        key = (current_system, current_item)
        if key not in check_items_map:
            continue
        
        check_item = check_items_map[key]
        
        # 각 날짜별 체크 기록 생성
        for date_col_idx, date_col_name in date_columns:
            if len(row) <= date_col_idx:
                continue
            
            status_str = row[date_col_idx].strip() if len(row) > date_col_idx else ""
            
            # 확인자 찾기 (날짜 컬럼 다음의 확인자 컬럼)
            checker_name = None
            checker_col_idx = date_col_idx + 1
            if checker_col_idx < len(row) and row[checker_col_idx].strip():
                checker_name = row[checker_col_idx].strip()
            
            if not status_str or status_str.upper() not in ['PASS', 'FAIL', 'P', 'F', 'OK', 'NG', 'Fail']:
                continue
            
            # 날짜 계산
            check_date = parse_week_info(date_col_name)
            if not check_date:
                continue
            
            # 상태 정규화
            status = normalize_status(status_str)
            
            # 확인자 찾기
            user = None
            if checker_name:
                user = user_map.get(checker_name)
                if not user:
                    # 부분 매칭 시도
                    for db_name, db_user in user_map.items():
                        if checker_name in db_name or db_name in checker_name:
                            user = db_user
                            break
            else:
                # 기본 확인자 사용
                if len(row) > checker_idx and row[checker_idx].strip():
                    default_checker = row[checker_idx].strip().split(',')[0].strip()
                    user = user_map.get(default_checker)
                    if not user:
                        for db_name, db_user in user_map.items():
                            if default_checker in db_name or db_name in default_checker:
                                user = db_user
                                break
            
            if not user:
                continue
            
            # 이슈사항을 notes에 저장
            notes = None
            if issue_column_idx and len(row) > issue_column_idx:
                issue = row[issue_column_idx].strip()
                if issue:
                    notes = issue
            
            # 기존 기록 확인
            existing_record = db.query(ChecklistRecord).filter(
                ChecklistRecord.user_id == user.id,
                ChecklistRecord.check_item_id == check_item.id,
                ChecklistRecord.check_date == check_date
            ).first()
            
            if existing_record:
                existing_record.status = status
                if notes:
                    existing_record.notes = notes
            else:
                new_record = ChecklistRecord(
                    user_id=user.id,
                    check_item_id=check_item.id,
                    check_date=check_date,
                    status=status,
                    notes=notes
                )
                db.add(new_record)
                records_created += 1
    
    db.commit()
    print(f"체크 기록 {records_created}개 생성 완료\n")
    
    print("=" * 50)
    print("CSV 데이터 임포트 완료!")
    print("=" * 50)
    print(f"\n생성된 데이터:")
    print(f"  - 시스템: {len(systems_data)}개")
    print(f"  - 사용자: {len(user_map)}명")
    print(f"  - 체크 항목: {len(check_items_map)}개")
    print(f"  - 체크 기록: {records_created}개")
    print(f"  - 특이사항: {db.query(SpecialNote).count()}개")
    print(f"  - 사용자-시스템 담당 관계: {db.query(UserSystemAssignment).count()}개")

except Exception as e:
    print(f"\n오류 발생: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
