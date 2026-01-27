from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from services.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True, index=True)  # 사번을 primary key로 사용
    user_name = Column(String(100), nullable=False)
    user_email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    # 조직 정보
    division = Column(String(100), nullable=True)  # 부문 (본부장만 존재)
    general_headquarters = Column(String(100), nullable=True)  # 총괄본부 (팀장 이상 존재)
    department = Column(String(100), nullable=True)  # 부서 (파트장/팀원만 존재, 이전 headquarters와 동일)
    position = Column(String(50), nullable=True)  # 직위
    role = Column(String(50), nullable=True)  # 직책
    console_role = Column(Boolean, default=False, nullable=False)  # 콘솔 페이지 접근 권한 (관리자)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class System(Base):
    __tablename__ = "systems"
    
    system_id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String(100), nullable=False)
    system_description = Column(Text)
    has_dev = Column(Boolean, default=False, nullable=False)
    has_stg = Column(Boolean, default=False, nullable=False)
    has_prd = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CheckItem(Base):
    __tablename__ = "check_items"
    
    item_id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("systems.system_id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String(200), nullable=False)
    item_description = Column(Text)
    environment = Column(String(10), nullable=False, default="prd")  # 'dev', 'stg', 'prd'
    status = Column(String(20), default="active", nullable=False)  # 'active' or 'deleted' (soft delete)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'deleted')", name="check_item_status"),
        CheckConstraint("environment IN ('dev', 'stg', 'prd')", name="check_item_environment"),
        UniqueConstraint("system_id", "item_name", "environment", name="uq_check_item_system_name_env"),
    )

class UserSystemAssignment(Base):
    __tablename__ = "user_system_assignments"
    
    id = Column("assign_id", Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems.system_id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("check_items.item_id", ondelete="CASCADE"), nullable=False)  # 체크 항목 ID (외래 키)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "system_id", "item_id", name="uq_user_system_assignment"),
    )

class ChecklistRecord(Base):
    __tablename__ = "checklist_records"
    
    records_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    check_item_id = Column("item_id", Integer, ForeignKey("check_items.item_id", ondelete="CASCADE"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems.system_id", ondelete="CASCADE"), nullable=True)  # 시스템 ID (외래 키, 성능 향상을 위해 denormalized)
    check_date = Column(Date, nullable=False)
    environment = Column(String(10), nullable=False, default="prd")  # 'dev', 'stg', 'prd'
    status = Column(String(10), nullable=False)
    fail_notes = Column(Text)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('PASS', 'FAIL')", name="check_status"),
        CheckConstraint("environment IN ('dev', 'stg', 'prd')", name="check_record_environment"),
        UniqueConstraint("item_id", "check_date", "environment", name="uq_checklist_record_item_date_env"),
    )

class ChecklistRecordLog(Base):
    """체크리스트 기록 로그 테이블 - 모든 액션을 로그로 기록"""
    __tablename__ = "checklist_records_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    check_item_id = Column(Integer, ForeignKey("check_items.item_id", ondelete="CASCADE"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems.system_id", ondelete="CASCADE"), nullable=True)  # 시스템 ID (외래 키, 성능 향상을 위해 denormalized)
    check_date = Column(Date, nullable=False)
    environment = Column(String(10), nullable=False, default="prd")  # 'dev', 'stg', 'prd'
    status = Column(String(10), nullable=False)  # PASS or FAIL
    fail_notes = Column(Text)
    action = Column(String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('PASS', 'FAIL')", name="check_log_status"),
        CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE')", name="check_log_action"),
        CheckConstraint("environment IN ('dev', 'stg', 'prd')", name="check_log_environment"),
    )

class SubstituteAssignment(Base):
    """대체 담당자 할당 테이블 - 시스템 단위로 대체 담당자 요청"""
    __tablename__ = "substitute_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    original_user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # 원래 담당자
    substitute_user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # 대체 담당자
    system_id = Column(Integer, ForeignKey("systems.system_id", ondelete="CASCADE"), nullable=False)  # 시스템 ID
    start_date = Column(Date, nullable=False)  # 대체 시작일
    end_date = Column(Date, nullable=False)  # 대체 종료일
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_date_range"),
    )

class SubstituteAssignmentLog(Base):
    """대체 담당자 할당 로그 테이블 - substitute_assignments의 모든 변경 이력 기록"""
    __tablename__ = "substitute_assignments_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    substitute_assignment_id = Column(Integer, ForeignKey("substitute_assignments.id", ondelete="SET NULL"), nullable=True)  # 삭제된 경우를 위해 nullable
    action = Column(String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    changed_by_user_id = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)  # 변경한 사용자
    old_data = Column(Text, nullable=True)  # 변경 전 데이터 (JSON 문자열)
    new_data = Column(Text, nullable=True)  # 변경 후 데이터 (JSON 문자열)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE')", name="substitute_assignment_log_action"),
    )

class AdminLog(Base):
    """관리자 작업 로그 테이블 - 시스템/항목/담당자 관리 작업 로그"""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=False)  # 작업한 관리자 (사용자 삭제 시에도 로그 보존)
    action = Column(String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    entity_type = Column(String(50), nullable=False)  # 'system', 'check_item', 'assignment'
    entity_id = Column(Integer, nullable=True)  # 대상 엔티티 ID (시스템 ID, 항목 ID, 배정 ID 등)
    environment = Column(String(10), nullable=True)  # 'dev', 'stg', 'prd' (assignment 등 환경별 구분이 필요한 경우)
    old_data = Column(Text, nullable=True)  # 변경 전 데이터 (JSON 문자열)
    new_data = Column(Text, nullable=True)  # 변경 후 데이터 (JSON 문자열)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE')", name="admin_log_action"),
        CheckConstraint("entity_type IN ('system', 'check_item', 'assignment')", name="admin_log_entity_type"),
        CheckConstraint("environment IN ('dev', 'stg', 'prd') OR environment IS NULL", name="admin_log_environment"),
    )

# SpecialNote 모델은 더 이상 사용하지 않습니다.
# special_notes 테이블의 데이터는 check_items.description으로 통합되었습니다.
# 
# class SpecialNote(Base):
#     __tablename__ = "special_notes"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     check_item_id = Column(Integer, ForeignKey("check_items.item_id", ondelete="CASCADE"), nullable=False)
#     note_text = Column(Text, nullable=False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

