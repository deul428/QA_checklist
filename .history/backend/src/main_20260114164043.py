from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv

from services.database import get_db, engine, Base
from models.models import User, System, CheckItem, UserSystemAssignment, ChecklistRecord
from services.schemas import (
    UserLogin, UserResponse, SystemResponse, CheckItemResponse,
    ChecklistSubmit, ChecklistRecordResponse, PasswordChange
)
from services.auth import verify_password, get_password_hash, create_access_token, get_current_user
from services.scheduler import init_scheduler

load_dotenv()

app = FastAPI(title="DX본부 시스템 체크리스트", version="1.0.0")

# 애플리케이션 시작 시 데이터베이스 테이블 생성
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("데이터베이스 연결 성공 및 테이블 생성 완료")
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        print("데이터베이스가 설정되지 않았습니다. .env 파일을 확인하세요.")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:5173"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# 스케줄러 초기화
init_scheduler()

@app.get("/")
async def root():
    return {"message": "DX본부 시스템 체크리스트 API"}

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """스케줄러 상태 확인"""
    from services.scheduler import scheduler
    jobs = []
    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }

@app.post("/api/scheduler/test")
async def test_scheduler():
    """스케줄러 수동 테스트 (관리자용)"""
    from services.scheduler import check_unchecked_items
    try:
        check_unchecked_items()
        return {"message": "스케줄러 테스트가 성공적으로 실행되었습니다."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스케줄러 테스트 중 오류 발생: {str(e)}"
        )

@app.post("/api/auth/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """사번 기반 로그인"""
    user = db.query(User).filter(User.employee_id == form_data.username).first()
    
    # if not user or not verify_password(form_data.password, user.password_hash):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="사번 또는 비밀번호가 올바르지 않습니다",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    
    access_token = create_access_token(data={"sub": user.employee_id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "employee_id": user.employee_id,
            "name": user.name,
            "email": user.email
        }
    }

@app.get("/api/user/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 로그인한 사용자 정보"""
    return current_user

@app.post("/api/user/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    # 현재 비밀번호 확인
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    # 새 비밀번호로 변경
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다"}

@app.get("/api/user/systems", response_model=List[SystemResponse])
async def get_user_systems(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자가 담당하는 시스템 목록"""
    assignments = db.query(UserSystemAssignment).filter(
        UserSystemAssignment.user_id == current_user.id
    ).all()
    
    system_ids = [assignment.system_id for assignment in assignments]
    systems = db.query(System).filter(System.id.in_(system_ids)).all()
    
    return systems

@app.get("/api/systems/{system_id}/check-items", response_model=List[CheckItemResponse])
async def get_check_items(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """시스템의 체크 항목 목록 (특이사항 포함)"""
    # 권한 확인
    assignment = db.query(UserSystemAssignment).filter(
        UserSystemAssignment.user_id == current_user.id,
        UserSystemAssignment.system_id == system_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 시스템에 대한 접근 권한이 없습니다"
        )
    
    check_items = db.query(CheckItem).filter(
        CheckItem.system_id == system_id
    ).order_by(CheckItem.order_index).all()
    
    return check_items

@app.get("/api/checklist/today", response_model=List[ChecklistRecordResponse])
async def get_today_checklist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """오늘 날짜의 체크리스트 기록 조회
    
    확인자가 여러 명인 경우, 한 명이 체크하면 다른 확인자들도 체크된 것으로 보임.
    따라서 user_id 필터 없이 check_item_id와 check_date만으로 조회.
    """
    today = date.today()
    
    # 사용자가 담당하는 시스템의 체크 항목 ID 목록
    assignments = db.query(UserSystemAssignment).filter(
        UserSystemAssignment.user_id == current_user.id
    ).all()
    system_ids = [a.system_id for a in assignments]
    check_item_ids = [
        item.id for item in db.query(CheckItem).filter(
            CheckItem.system_id.in_(system_ids)
        ).all()
    ]
    
    # 오늘 날짜에 체크된 기록 조회 (다른 사람이 체크한 것도 포함)
    records = db.query(ChecklistRecord).filter(
        ChecklistRecord.check_item_id.in_(check_item_ids),
        ChecklistRecord.check_date == today
    ).all()
    
    return records

@app.post("/api/checklist/submit", response_model=dict)
async def submit_checklist(
    checklist_data: ChecklistSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """체크리스트 제출 (PASS/FAIL 저장)"""
    today = date.today()
    
    for item in checklist_data.items:
        # 체크 항목 권한 확인
        check_item = db.query(CheckItem).filter(CheckItem.id == item.check_item_id).first()
        if not check_item:
            continue
        
        assignment = db.query(UserSystemAssignment).filter(
            UserSystemAssignment.user_id == current_user.id,
            UserSystemAssignment.system_id == check_item.system_id
        ).first()
        
        if not assignment:
            continue
        
        # 기존 기록 확인 및 업데이트 또는 생성
        # 확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
        # 따라서 user_id 필터 없이 check_item_id와 check_date만으로 확인.
        existing_record = db.query(ChecklistRecord).filter(
            ChecklistRecord.check_item_id == item.check_item_id,
            ChecklistRecord.check_date == today
        ).first()
        
        if existing_record:
            # 기존 기록이 있으면 업데이트 (누가 체크했는지는 기록)
            existing_record.status = item.status
            existing_record.notes = item.notes
            existing_record.checked_at = datetime.now()
            # 체크한 사람 정보도 업데이트 (같은 사람이 다시 체크한 경우)
            existing_record.user_id = current_user.id
        else:
            # 새 기록 생성
            new_record = ChecklistRecord(
                user_id=current_user.id,
                check_item_id=item.check_item_id,
                check_date=today,
                status=item.status,
                notes=item.notes
            )
            db.add(new_record)
    
    db.commit()
    return {"message": "체크리스트가 성공적으로 저장되었습니다"}

@app.get("/api/checklist/unchecked", response_model=List[dict])
async def get_unchecked_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """오늘 체크되지 않은 항목 조회
    
    확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
    따라서 user_id 필터 없이 check_item_id와 check_date만으로 확인.
    """
    today = date.today()
    
    # 사용자가 담당하는 시스템의 모든 체크 항목
    assignments = db.query(UserSystemAssignment).filter(
        UserSystemAssignment.user_id == current_user.id
    ).all()
    
    system_ids = [a.system_id for a in assignments]
    all_items = db.query(CheckItem).filter(CheckItem.system_id.in_(system_ids)).all()
    
    # 오늘 체크된 항목 (다른 사람이 체크한 것도 포함)
    checked_records = db.query(ChecklistRecord).filter(
        ChecklistRecord.check_date == today
    ).all()
    checked_item_ids = {r.check_item_id for r in checked_records}
    
    # 체크되지 않은 항목
    unchecked_items = [
        {
            "check_item_id": item.id,
            "item_name": item.item_name,
            "system_id": item.system_id,
            "system_name": db.query(System).filter(System.id == item.system_id).first().system_name
        }
        for item in all_items
        if item.id not in checked_item_ids
    ]
    
    return unchecked_items

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

