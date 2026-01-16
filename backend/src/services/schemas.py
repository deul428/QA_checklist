from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime

class UserLogin(BaseModel):
    employee_id: str
    password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    email: str
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
    id: int
    system_name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class CheckItemResponse(BaseModel):
    id: int
    system_id: int
    item_name: str
    description: Optional[str] = None
    order_index: int
    
    class Config:
        from_attributes = True

class CheckItemSubmit(BaseModel):
    check_item_id: int
    status: str  # PASS or FAIL
    notes: Optional[str] = None

class ChecklistSubmit(BaseModel):
    items: List[CheckItemSubmit]

class ChecklistRecordResponse(BaseModel):
    id: int
    user_id: int
    check_item_id: int
    check_date: date
    status: str
    notes: Optional[str] = None
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
    notes: Optional[str] = None
    fail_time: datetime
    user_id: int
    user_name: str
    employee_id: str
    is_resolved: bool  # fail에서 pass로 변경되었는지
    resolved_date: Optional[date] = None
    resolved_time: Optional[datetime] = None

class ExcelExportRequest(BaseModel):
    start_date: date
    end_date: date

