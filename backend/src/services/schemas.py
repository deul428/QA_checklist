from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime


class UserLogin(BaseModel):
    user_id: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    division: Optional[str] = None
    general_headquarters: Optional[str] = None
    headquarters: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    console_role: bool = False

    class Config:
        from_attributes = True


class SystemResponse(BaseModel):
    system_id: int
    system_name: str
    system_description: Optional[str] = None
    has_dev: bool = False
    has_stg: bool = False
    has_prd: bool = False

    class Config:
        from_attributes = True


class CheckItemResponse(BaseModel):
    item_id: int
    system_id: int
    item_name: str
    item_description: Optional[str] = None
    environment: str = "prd"  # 'dev', 'stg', 'prd'
    status: str = "active"  # 'active' or 'deleted'

    class Config:
        from_attributes = True


class CheckItemCreate(BaseModel):
    system_id: int
    item_name: str
    item_description: Optional[str] = None
    environment: str = "prd"  # 'dev', 'stg', 'prd' (필수)
    apply_to_all_environments: Optional[bool] = False  # 일괄 처리 여부
    user_ids: Optional[List[str]] = None  # 담당자 ID 목록 (항목 생성 시 함께 배정)


class CheckItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_description: Optional[str] = None
    status: Optional[str] = None
    apply_to_all_environments: Optional[bool] = False  # 일괄 처리 여부


class AssignmentCreate(BaseModel):
    system_id: int
    check_item_id: int
    user_ids: List[str]  # 여러 명의 담당자 배정 가능 (user_id 리스트)


class CheckItemSubmit(BaseModel):
    check_item_id: int
    status: str  # PASS or FAIL
    fail_notes: Optional[str] = None
    environment: str = "prd"  # 'dev', 'stg', 'prd'


class ChecklistSubmit(BaseModel):
    items: List[CheckItemSubmit]


class ChecklistRecordResponse(BaseModel):
    records_id: int
    user_id: str
    check_item_id: int
    system_id: Optional[int] = None  # 시스템 ID (denormalized)
    check_date: date
    environment: str = "prd"  # 'dev', 'stg', 'prd'
    status: str
    fail_notes: Optional[str] = None
    checked_at: datetime

    class Config:
        from_attributes = True


class TestEmailSchedule(BaseModel):
    hour: int  # 0-23
    minute: int  # 0-59


class ConsoleStatsResponse(BaseModel):
    pass_count: int
    fail_count: int
    unchecked_count: int


class ConsoleFailItemResponse(BaseModel):
    id: int
    system_id: int
    system_name: str
    check_item_id: int
    item_name: str
    environment: str = "prd"  # 'dev', 'stg', 'prd'
    fail_notes: Optional[str] = None
    fail_time: datetime
    user_id: str
    user_name: str
    is_resolved: bool  # fail에서 pass로 변경되었는지
    resolved_date: Optional[date] = None
    resolved_time: Optional[datetime] = None


class ConsoleAllItemResponse(BaseModel):
    id: int
    system_id: int
    system_name: str
    check_item_id: int
    item_name: str
    environment: str = "prd"
    status: str  # 'PASS', 'FAIL', '미점검'
    fail_notes: Optional[str] = None
    fail_time: Optional[datetime] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    is_resolved: bool
    resolved_time: Optional[datetime] = None
    checked_at: Optional[datetime] = None


class ExcelExportRequest(BaseModel):
    start_date: date
    end_date: date


class SubstituteAssignmentCreate(BaseModel):
    substitute_user_id: str  # 대체 담당자 user_id
    system_id: int  # 시스템 ID
    start_date: date  # 대체 시작일
    end_date: date  # 대체 종료일


class SubstituteAssignmentResponse(BaseModel):
    id: int
    original_user_id: str
    original_user_name: str
    substitute_user_id: str
    substitute_user_name: str
    system_id: int
    system_name: str
    start_date: date
    end_date: date
    created_at: datetime
    is_active: (
        bool  # 현재 활성화되어 있는지 (오늘 날짜가 start_date와 end_date 사이인지)
    )

    class Config:
        from_attributes = True


class ConsistencyIssueResponse(BaseModel):
    """일관성 검증 결과 이슈"""
    issue: str


class ConsistencyCheckResponse(BaseModel):
    """일관성 검증 결과"""
    check_item_id: int
    check_date: date
    environment: str
    is_consistent: bool
    record_exists: bool
    latest_log_exists: bool
    latest_log_action: Optional[str] = None
    issues: List[str]
