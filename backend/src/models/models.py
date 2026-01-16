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
    # 조직 정보
    division = Column(String(100), nullable=True)  # 부문 (본부장만 존재)
    general_headquarters = Column(String(100), nullable=True)  # 총괄본부 (팀장 이상 존재)
    department = Column(String(100), nullable=True)  # 부서 (파트장/팀원만 존재, 이전 headquarters와 동일)
    position = Column(String(50), nullable=True)  # 직위
    role = Column(String(50), nullable=True)  # 직책
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
    user_name = Column(String(100), nullable=False)  # 사용자 이름 (denormalization)
    system_id = Column(Integer, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String(200), nullable=False)  # 체크 항목 이름 (denormalization)
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

class ChecklistRecordLog(Base):
    """체크리스트 기록 로그 테이블 - 모든 액션을 로그로 기록"""
    __tablename__ = "checklist_records_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    check_item_id = Column(Integer, ForeignKey("check_items.id", ondelete="CASCADE"), nullable=False)
    check_date = Column(Date, nullable=False)
    status = Column(String(10), nullable=False)  # PASS or FAIL
    notes = Column(Text)
    action = Column(String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('PASS', 'FAIL')", name="check_log_status"),
        CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE')", name="check_log_action"),
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

