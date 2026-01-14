from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from services.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class System(Base):
    __tablename__ = "systems"
    
    id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CheckItem(Base):
    __tablename__ = "check_items"
    
    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSystemAssignment(Base):
    __tablename__ = "user_system_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChecklistRecord(Base):
    __tablename__ = "checklist_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    check_item_id = Column(Integer, ForeignKey("check_items.id", ondelete="CASCADE"), nullable=False)
    check_date = Column(Date, nullable=False)
    status = Column(String(10), nullable=False)
    notes = Column(Text)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('PASS', 'FAIL')", name="check_status"),
    )

# SpecialNote 모델은 더 이상 사용하지 않습니다.
# special_notes 테이블의 데이터는 check_items.description으로 통합되었습니다.
# 
# class SpecialNote(Base):
#     __tablename__ = "special_notes"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     check_item_id = Column(Integer, ForeignKey("check_items.id", ondelete="CASCADE"), nullable=False)
#     note_text = Column(Text, nullable=False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

