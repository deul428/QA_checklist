"""
체크리스트 기록 및 로그 관리를 위한 헬퍼 함수

이 모듈은 checklist_records와 checklist_records_logs 테이블의
일관성을 보장하고 코드 중복을 줄이기 위한 헬퍼 함수를 제공합니다.
"""

from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
import pytz
from models.models import ChecklistRecord, ChecklistRecordLog, CheckItem


def get_korea_now():
    """한국 시간 기준 현재 시간 반환"""
    kst = pytz.timezone("Asia/Seoul")
    return datetime.now(kst)


def create_or_update_checklist_record(
    db: Session,
    user_id: str,
    check_item_id: int,
    system_id: int,
    check_date: date,
    environment: str,
    status: str,
    fail_notes: Optional[str] = None,
) -> tuple[ChecklistRecord, ChecklistRecordLog]:
    """
    체크리스트 기록을 생성하거나 업데이트하고 로그를 기록합니다.
    
    이 함수는 checklist_records와 checklist_records_logs 테이블의
    일관성을 보장하기 위해 두 테이블을 함께 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 체크한 사용자 ID
        check_item_id: 체크 항목 ID
        system_id: 시스템 ID
        check_date: 체크 날짜
        environment: 환경 ('dev', 'stg', 'prd')
        status: 상태 ('PASS' 또는 'FAIL')
        fail_notes: 실패 사유 (선택사항)
    
    Returns:
        (ChecklistRecord, ChecklistRecordLog) 튜플
        - ChecklistRecord: 생성 또는 업데이트된 기록
        - ChecklistRecordLog: 생성된 로그 엔트리
    
    Raises:
        ValueError: 잘못된 파라미터가 전달된 경우
    """
    # 파라미터 검증
    if status not in ["PASS", "FAIL"]:
        raise ValueError(f"status는 'PASS' 또는 'FAIL'이어야 합니다. 받은 값: {status}")
    
    if environment not in ["dev", "stg", "prd"]:
        raise ValueError(f"environment는 'dev', 'stg', 'prd' 중 하나여야 합니다. 받은 값: {environment}")
    
    # 기존 기록 확인
    existing_record = (
        db.query(ChecklistRecord)
        .filter(
            ChecklistRecord.check_item_id == check_item_id,
            ChecklistRecord.check_date == check_date,
            ChecklistRecord.environment == environment,
        )
        .first()
    )
    
    if existing_record:
        # 기존 기록 업데이트
        action = "UPDATE"
        old_status = existing_record.status
        
        existing_record.status = status
        existing_record.fail_notes = fail_notes
        existing_record.checked_at = get_korea_now()
        existing_record.system_id = system_id  # system_id 업데이트 (일관성 유지)
        existing_record.user_id = user_id  # 체크한 사람 정보 업데이트
        
        record = existing_record
    else:
        # 새 기록 생성
        action = "CREATE"
        record = ChecklistRecord(
            user_id=user_id,
            check_item_id=check_item_id,
            system_id=system_id,
            check_date=check_date,
            environment=environment,
            status=status,
            fail_notes=fail_notes,
        )
        db.add(record)
    
    # 로그 기록
    log_entry = ChecklistRecordLog(
        user_id=user_id,
        check_item_id=check_item_id,
        system_id=system_id,
        check_date=check_date,
        environment=environment,
        status=status,
        fail_notes=fail_notes,
        action=action,
    )
    db.add(log_entry)
    
    return record, log_entry


def verify_checklist_consistency(
    db: Session,
    check_item_id: int,
    check_date: date,
    environment: str,
) -> dict:
    """
    checklist_records와 checklist_records_logs 간의 일관성을 검증합니다.
    
    Args:
        db: 데이터베이스 세션
        check_item_id: 체크 항목 ID
        check_date: 체크 날짜
        environment: 환경 ('dev', 'stg', 'prd')
    
    Returns:
        dict: 검증 결과
        - is_consistent: bool - 일관성 여부
        - record: Optional[ChecklistRecord] - 현재 기록
        - latest_log: Optional[ChecklistRecordLog] - 최신 로그
        - issues: List[str] - 발견된 문제 목록
    """
    issues = []
    
    # 현재 기록 조회
    record = (
        db.query(ChecklistRecord)
        .filter(
            ChecklistRecord.check_item_id == check_item_id,
            ChecklistRecord.check_date == check_date,
            ChecklistRecord.environment == environment,
        )
        .first()
    )
    
    # 최신 로그 조회
    latest_log = (
        db.query(ChecklistRecordLog)
        .filter(
            ChecklistRecordLog.check_item_id == check_item_id,
            ChecklistRecordLog.check_date == check_date,
            ChecklistRecordLog.environment == environment,
        )
        .order_by(ChecklistRecordLog.created_at.desc())
        .first()
    )
    
    # 일관성 검증
    if record and latest_log:
        # 기록과 로그의 상태가 일치하는지 확인
        if record.status != latest_log.status:
            issues.append(
                f"기록 상태({record.status})와 최신 로그 상태({latest_log.status})가 일치하지 않습니다."
            )
        
        # 기록과 로그의 fail_notes가 일치하는지 확인
        record_notes = record.fail_notes or ""
        log_notes = latest_log.fail_notes or ""
        if record_notes != log_notes:
            issues.append(
                f"기록의 fail_notes와 최신 로그의 fail_notes가 일치하지 않습니다."
            )
        
        # 최신 로그가 CREATE 또는 UPDATE인지 확인
        if latest_log.action not in ["CREATE", "UPDATE"]:
            issues.append(
                f"최신 로그의 액션이 {latest_log.action}입니다. CREATE 또는 UPDATE여야 합니다."
            )
    
    elif record and not latest_log:
        # 기록은 있지만 로그가 없는 경우
        issues.append("기록은 존재하지만 해당하는 로그가 없습니다.")
    
    elif not record and latest_log:
        # 로그는 있지만 기록이 없는 경우 (DELETE 액션인 경우 정상)
        if latest_log.action != "DELETE":
            issues.append(
                f"로그는 존재하지만 기록이 없습니다. 최신 로그 액션: {latest_log.action}"
            )
    
    is_consistent = len(issues) == 0
    
    return {
        "is_consistent": is_consistent,
        "record": record,
        "latest_log": latest_log,
        "issues": issues,
    }


def delete_checklist_record_with_log(
    db: Session,
    check_item_id: int,
    check_date: date,
    environment: str,
    user_id: str,
) -> Optional[ChecklistRecordLog]:
    """
    체크리스트 기록을 삭제하고 DELETE 액션 로그를 기록합니다.
    
    Args:
        db: 데이터베이스 세션
        check_item_id: 체크 항목 ID
        check_date: 체크 날짜
        environment: 환경 ('dev', 'stg', 'prd')
        user_id: 삭제한 사용자 ID
    
    Returns:
        ChecklistRecordLog: 생성된 DELETE 로그 엔트리, 기록이 없으면 None
    """
    # 기존 기록 확인
    existing_record = (
        db.query(ChecklistRecord)
        .filter(
            ChecklistRecord.check_item_id == check_item_id,
            ChecklistRecord.check_date == check_date,
            ChecklistRecord.environment == environment,
        )
        .first()
    )
    
    if not existing_record:
        return None
    
    # 삭제 전 상태 저장
    old_status = existing_record.status
    old_fail_notes = existing_record.fail_notes
    system_id = existing_record.system_id
    
    # 기록 삭제
    db.delete(existing_record)
    
    # DELETE 로그 기록
    log_entry = ChecklistRecordLog(
        user_id=user_id,
        check_item_id=check_item_id,
        system_id=system_id,
        check_date=check_date,
        environment=environment,
        status=old_status,  # 삭제 전 상태 저장
        fail_notes=old_fail_notes,  # 삭제 전 사유 저장
        action="DELETE",
    )
    db.add(log_entry)
    
    return log_entry

