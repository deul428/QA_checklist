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

    class Config:
        from_attributes = True


class CheckItemResponse(BaseModel):
    item_id: int
    system_id: int
    item_name: str
    item_description: Optional[str] = None
    status: str = "active"  # 'active' or 'deleted'

    class Config:
        from_attributes = True


class CheckItemCreate(BaseModel):
    system_id: int
    item_name: str
    item_description: Optional[str] = None


class CheckItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_description: Optional[str] = None
    status: Optional[str] = None


class AssignmentCreate(BaseModel):
    system_id: int
    check_item_id: int
    user_ids: List[str]  # 여러 명의 담당자 배정 가능 (user_id 리스트)


class CheckItemSubmit(BaseModel):
    check_item_id: int
    status: str  # PASS or FAIL
    fail_notes: Optional[str] = None


class ChecklistSubmit(BaseModel):
    items: List[CheckItemSubmit]


class ChecklistRecordResponse(BaseModel):
    records_id: int
    user_id: str
    check_item_id: int
    check_date: date
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
    fail_notes: Optional[str] = None
    fail_time: datetime
    user_id: str
    user_name: str
    is_resolved: bool  # fail에서 pass로 변경되었는지
    resolved_date: Optional[date] = None
    resolved_time: Optional[datetime] = None


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
