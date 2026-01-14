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
    
    class Config:
        from_attributes = True

class SystemResponse(BaseModel):
    id: int
    system_name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class SpecialNoteResponse(BaseModel):
    id: int
    note_text: str
    
    class Config:
        from_attributes = True

class CheckItemResponse(BaseModel):
    id: int
    system_id: int
    item_name: str
    description: Optional[str] = None
    order_index: int
    special_notes: List[str] = []

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

