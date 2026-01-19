from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
from typing import List, Optional
import os
import io
from dotenv import load_dotenv

from services.database import get_db, engine, Base
from models.models import (
    User,
    System,
    CheckItem,
    UserSystemAssignment,
    ChecklistRecord,
    ChecklistRecordLog,
)
from services.schemas import (
    UserLogin,
    UserResponse,
    SystemResponse,
    CheckItemResponse,
    ChecklistSubmit,
    ChecklistRecordResponse,
    PasswordChange,
    TestEmailSchedule,
    ConsoleStatsResponse,
    ConsoleFailItemResponse,
    ExcelExportRequest,
)
from services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from services.scheduler import init_scheduler, get_korea_today

load_dotenv()

app = FastAPI(title="DX본부 시스템 체크리스트", version="1.0.0")


# 애플리케이션 시작 시 데이터베이스 테이블 생성 및 스케줄러 초기화
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("데이터베이스 연결 성공 및 테이블 생성 완료")
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        print("데이터베이스가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    # 스케줄러 초기화 (startup 이벤트에서 실행)
    try:
        init_scheduler()
        print("스케줄러 초기화 완료")
    except Exception as e:
        print(f"스케줄러 초기화 오류: {e}")
        import traceback
        traceback.print_exc()


# CORS 설정
# 개발 환경: 모든 localhost 포트 허용
allowed_origins = [
    "http://localhost:3003",
    "http://localhost:5173",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:5173",
    "http://192.10.10.206:3003",
    "http://192.10.10.206:5173",
]

# 환경 변수에서 추가 origin 허용
if os.getenv("CORS_ORIGINS"):
    additional_origins = [
        origin.strip() for origin in os.getenv("CORS_ORIGINS").split(",")
    ]
    allowed_origins.extend(additional_origins)

# 개발 환경에서는 일반적인 개발 포트들을 모두 허용
# React 개발 서버는 보통 3000-3010, Vite는 5173 등 사용
for port in range(3000, 3011):
    allowed_origins.append(f"http://localhost:{port}")
    allowed_origins.append(f"http://127.0.0.1:{port}")
    allowed_origins.append(f"http://192.10.10.206:{port}")

# Vite 기본 포트
allowed_origins.append("http://localhost:5173")
allowed_origins.append("http://127.0.0.1:5173")
allowed_origins.append("http://192.10.10.206:5173")

# 운영 환경에서는 특정 도메인만 허용하도록 주의
is_production = os.getenv("ENV") == "production"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


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
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )

    return {"running": scheduler.running, "jobs": jobs}


@app.delete("/api/scheduler/jobs/{job_id}")
async def cancel_scheduled_job(job_id: str):
    """예약된 작업 취소 (개발자용)"""
    from services.scheduler import scheduler

    try:
        if not scheduler.running:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="스케줄러가 실행되지 않았습니다.",
            )

        # 작업이 존재하는지 확인
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"작업 ID '{job_id}'를 찾을 수 없습니다.",
            )

        job_name = job.name
        # 작업 취소
        scheduler.remove_job(job_id)

        return {
            "message": f"작업 '{job_name}' (ID: {job_id})이 취소되었습니다.",
            "job_id": job_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작업 취소 중 오류 발생: {str(e)}",
        )


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
            detail=f"스케줄러 테스트 중 오류 발생: {str(e)}",
        )


@app.post("/api/scheduler/test-email")
async def test_email_send(schedule: TestEmailSchedule):
    """테스트 메일 스케줄링 (실제 DB의 담당자 이메일 주소 사용)

    시간을 지정하면 해당 시간에 메일을 발송하도록 스케줄링합니다.
    실제 DB의 담당자 이메일 주소로 발송됩니다.
    """
    from services.scheduler import schedule_test_email, scheduler
    import pytz

    try:
        # 시간 유효성 검사
        if not (0 <= schedule.hour <= 23 and 0 <= schedule.minute <= 59):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시간은 0-23시, 분은 0-59분 사이여야 합니다.",
            )

        # 스케줄러가 실행 중인지 확인
        if not scheduler.running:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="스케줄러가 실행되지 않았습니다.",
            )

        # 스케줄링
        job_id, scheduled_time = schedule_test_email(schedule.hour, schedule.minute)

        kst = pytz.timezone("Asia/Seoul")
        scheduled_time_str = scheduled_time.astimezone(kst).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return {
            "message": f"테스트 메일이 {scheduled_time_str}에 발송되도록 스케줄링되었습니다.",
            "scheduled_time": scheduled_time_str,
            "job_id": job_id,
            "note": "실제 DB의 담당자 이메일 주소로 발송됩니다.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 메일 스케줄링 중 오류 발생: {str(e)}",
        )


@app.post("/api/scheduler/test-email-now")
async def test_email_send_now():
    """테스트 메일 즉시 발송 (실제 DB의 담당자 이메일 주소 사용)

    즉시 메일을 발송합니다. 스케줄링 없이 바로 전송됩니다.
    실제 DB의 담당자 이메일 주소로 발송됩니다.
    """
    from services.scheduler import send_test_email_scheduled

    try:
        # 즉시 발송
        send_test_email_scheduled()

        return {
            "message": "메일이 발송되었습니다.",
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "실제 DB의 담당자 이메일 주소로 발송되었습니다.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메일 발송 중 오류 발생: {str(e)}",
        )


@app.post("/api/auth/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
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
    
    # UserResponse 스키마를 사용하여 모든 필드 포함
    from services.schemas import UserResponse
    user_response = UserResponse(
        id=user.id,
        employee_id=user.employee_id,
        name=user.name,
        email=user.email,
        division=user.division,
        general_headquarters=user.general_headquarters,
        headquarters=user.department,  # department를 headquarters로도 반환 (프론트엔드 호환성)
        department=user.department,
        position=user.position,
        role=user.role,
        console_role=user.console_role,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response.model_dump(),
    }


@app.get("/api/user/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """현재 로그인한 사용자 정보"""
    return current_user


@app.post("/api/user/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """비밀번호 변경"""
    # 현재 비밀번호 확인
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="현재 비밀번호가 올바르지 않습니다",
        )

    # 새 비밀번호로 변경
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다"}


@app.get("/api/user/systems", response_model=List[SystemResponse])
async def get_user_systems(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """사용자가 담당하는 시스템 목록"""
    assignments = (
        db.query(UserSystemAssignment)
        .filter(UserSystemAssignment.user_id == current_user.id)
        .all()
    )

    system_ids = [assignment.system_id for assignment in assignments]
    systems = db.query(System).filter(System.id.in_(system_ids)).all()

    return systems


@app.get("/api/systems/{system_id}/check-items", response_model=List[CheckItemResponse])
async def get_check_items(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """시스템의 체크 항목 목록 (특이사항 포함)"""
    # 권한 확인
    assignment = (
        db.query(UserSystemAssignment)
        .filter(
            UserSystemAssignment.user_id == current_user.id,
            UserSystemAssignment.system_id == system_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 시스템에 대한 접근 권한이 없습니다",
        )

    check_items = (
        db.query(CheckItem)
        .filter(CheckItem.system_id == system_id)
        .order_by(CheckItem.order_index)
        .all()
    )

    return check_items


@app.get("/api/checklist/today", response_model=List[ChecklistRecordResponse])
async def get_today_checklist(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """오늘 날짜의 체크리스트 기록 조회

    확인자가 여러 명인 경우, 한 명이 체크하면 다른 확인자들도 체크된 것으로 보임.
    따라서 user_id 필터 없이 check_item_id와 check_date만으로 조회.
    """
    today = date.today()

    # 사용자가 담당하는 시스템의 체크 항목 ID 목록
    assignments = (
        db.query(UserSystemAssignment)
        .filter(UserSystemAssignment.user_id == current_user.id)
        .all()
    )
    system_ids = [a.system_id for a in assignments]
    check_item_ids = [
        item.id
        for item in db.query(CheckItem)
        .filter(CheckItem.system_id.in_(system_ids))
        .all()
    ]

    # 오늘 날짜에 체크된 기록 조회 (다른 사람이 체크한 것도 포함)
    records = (
        db.query(ChecklistRecord)
        .filter(
            ChecklistRecord.check_item_id.in_(check_item_ids),
            ChecklistRecord.check_date == today,
        )
        .all()
    )

    return records


@app.post("/api/checklist/submit", response_model=dict)
async def submit_checklist(
    checklist_data: ChecklistSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """체크리스트 제출 (PASS/FAIL 저장)"""
    today = date.today()

    for item in checklist_data.items:
        # 체크 항목 권한 확인
        check_item = (
            db.query(CheckItem).filter(CheckItem.id == item.check_item_id).first()
        )
        if not check_item:
            continue

        assignment = (
            db.query(UserSystemAssignment)
            .filter(
                UserSystemAssignment.user_id == current_user.id,
                UserSystemAssignment.system_id == check_item.system_id,
            )
            .first()
        )

        if not assignment:
            continue

        # 기존 기록 확인 및 업데이트 또는 생성
        # 확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
        # 따라서 user_id 필터 없이 check_item_id와 check_date만으로 확인.
        existing_record = (
            db.query(ChecklistRecord)
            .filter(
                ChecklistRecord.check_item_id == item.check_item_id,
                ChecklistRecord.check_date == today,
            )
            .first()
        )

        if existing_record:
            # 기존 기록이 있으면 업데이트 (누가 체크했는지는 기록)
            old_status = existing_record.status
            existing_record.status = item.status
            existing_record.notes = item.notes
            existing_record.checked_at = datetime.now()
            # 체크한 사람 정보도 업데이트 (같은 사람이 다시 체크한 경우)
            existing_record.user_id = current_user.id

            # 로그 기록 (UPDATE 액션)
            log_entry = ChecklistRecordLog(
                user_id=current_user.id,
                check_item_id=item.check_item_id,
                check_date=today,
                status=item.status,
                notes=item.notes,
                action="UPDATE",
            )
            db.add(log_entry)
        else:
            # 새 기록 생성
            new_record = ChecklistRecord(
                user_id=current_user.id,
                check_item_id=item.check_item_id,
                check_date=today,
                status=item.status,
                notes=item.notes,
            )
            db.add(new_record)

            # 로그 기록 (CREATE 액션)
            log_entry = ChecklistRecordLog(
                user_id=current_user.id,
                check_item_id=item.check_item_id,
                check_date=today,
                status=item.status,
                notes=item.notes,
                action="CREATE",
            )
            db.add(log_entry)

    db.commit()
    return {"message": "체크리스트가 성공적으로 저장되었습니다"}


def check_console_access(current_user: User):
    """console 페이지 접근 권한 체크 (DB의 console_role 컬럼 확인)"""
    if not current_user.console_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="console 페이지 접근 권한이 없습니다",
        )


@app.get("/api/console/stats", response_model=ConsoleStatsResponse)
async def get_console_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """console 페이지 통계 조회 (오늘 날짜 기준 pass/fail/미점검)"""
    check_console_access(current_user)

    today = get_korea_today()

    # 오늘 체크된 항목
    checked_records = (
        db.query(ChecklistRecord).filter(ChecklistRecord.check_date == today).all()
    )

    pass_count = sum(1 for r in checked_records if r.status == "PASS")
    fail_count = sum(1 for r in checked_records if r.status == "FAIL")

    # 모든 체크 항목 수
    all_items_count = db.query(CheckItem).count()
    unchecked_count = all_items_count - len(checked_records)

    return ConsoleStatsResponse(
        pass_count=pass_count,
        fail_count=fail_count,
        unchecked_count=unchecked_count,
    )


@app.get("/api/console/fail-items", response_model=List[ConsoleFailItemResponse])
async def get_console_fail_items(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """console 페이지 fail 항목 목록 조회

    오늘 날짜에 FAIL 상태가 된 모든 항목을 조회합니다.
    - 처음부터 FAIL인 경우
    - PASS에서 FAIL로 변경된 경우
    - FAIL에서 PASS로 변경되었다가 다시 FAIL로 변경된 경우
    """
    check_console_access(current_user)

    today = get_korea_today()

    # 오늘 날짜의 모든 로그를 시간순으로 조회
    all_logs = (
        db.query(ChecklistRecordLog)
        .filter(ChecklistRecordLog.check_date == today)
        .order_by(ChecklistRecordLog.created_at)  # 전체 로그를 시간순으로 정렬
        .all()
    )

    # 각 check_item_id별로 상태 변경 추적 (시간순으로 정렬된 로그를 항목별로 그룹화)
    item_status_history = (
        {}
    )  # {check_item_id: [(status, created_at, user_id, notes), ...]}

    for log in all_logs:
        if log.check_item_id not in item_status_history:
            item_status_history[log.check_item_id] = []
        item_status_history[log.check_item_id].append(
            (log.status, log.created_at, log.user_id, log.notes)
        )

    # 각 항목의 로그를 시간순으로 정렬 (혹시 모를 정렬 문제 방지)
    for check_item_id in item_status_history:
        item_status_history[check_item_id].sort(
            key=lambda x: x[1]
        )  # created_at 기준 정렬

    result = []

    for check_item_id, history in item_status_history.items():
        # 체크 항목 정보
        check_item = db.query(CheckItem).filter(CheckItem.id == check_item_id).first()
        if not check_item:
            continue

        # 시스템 정보
        system = db.query(System).filter(System.id == check_item.system_id).first()
        if not system:
            continue

        # 최종 상태 확인 (시간순으로 정렬된 마지막 로그의 상태)
        # history는 이미 시간순으로 정렬되어 있음
        final_status = history[-1][0]  # 마지막 로그의 상태

        # 최종 상태가 FAIL인 항목만 표시
        if final_status != "FAIL":
            continue

        # 첫 번째 FAIL 로그 찾기 (PASS -> FAIL 또는 처음부터 FAIL)
        first_fail_log = None
        for status, created_at, user_id, notes in history:
            if status == "FAIL":
                first_fail_log = (status, created_at, user_id, notes)
                break

        if not first_fail_log:
            continue

        # 사용자 정보 (첫 번째 FAIL을 기록한 사용자)
        user = db.query(User).filter(User.id == first_fail_log[2]).first()
        if not user:
            continue

        # FAIL 이후에 PASS로 변경되었는지 확인
        first_fail_time = first_fail_log[1]
        pass_after_fail = None
        for status, created_at, user_id, notes in history:
            if status == "PASS" and created_at > first_fail_time:
                pass_after_fail = (created_at, notes)
                break

        # PASS 이후에 다시 FAIL로 변경되었는지 확인
        is_resolved = False
        resolved_date = None
        resolved_time = None

        if pass_after_fail:
            # PASS 이후에 다시 FAIL이 있는지 확인
            pass_time = pass_after_fail[0]
            fail_after_pass = None
            for status, created_at, user_id, notes in history:
                if status == "FAIL" and created_at > pass_time:
                    fail_after_pass = (created_at, notes)
                    break

            if not fail_after_pass:
                # PASS 이후에 FAIL이 없으면 해결된 것으로 간주
                # 하지만 최종 상태가 FAIL이므로, 이 경우는 발생하지 않아야 함
                # 최종 상태가 FAIL이면 미해결로 처리
                is_resolved = False
                resolved_date = None
                resolved_time = None

        # 최신 FAIL 로그 정보 (최종 FAIL 상태)
        latest_fail_log = None
        for status, created_at, user_id, notes in reversed(history):
            if status == "FAIL":
                latest_fail_log = (created_at, notes)
                break

        if not latest_fail_log:
            latest_fail_log = (first_fail_log[1], first_fail_log[3])

        result.append(
            ConsoleFailItemResponse(
                id=check_item_id,  # check_item_id를 id로 사용
                system_id=system.id,
                system_name=system.system_name,
                check_item_id=check_item_id,
                item_name=check_item.item_name,
                notes=latest_fail_log[1] if latest_fail_log else first_fail_log[3],
                fail_time=first_fail_log[1],  # 첫 번째 FAIL 시간
                user_id=user.id,
                user_name=user.name,
                employee_id=user.employee_id,
                is_resolved=is_resolved,
                resolved_date=resolved_date,
                resolved_time=resolved_time,
            )
        )

    # fail_time 기준으로 정렬 (최신순)
    result.sort(key=lambda x: x.fail_time, reverse=True)

    print(f"[Console API] 오늘 FAIL 항목: {len(result)}개")
    for item in result:
        print(
            f"  - {item.item_name}: is_resolved={item.is_resolved}, fail_time={item.fail_time}"
        )

    return result


@app.get("/api/checklist/unchecked", response_model=List[dict])
async def get_unchecked_items(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """오늘 체크되지 않은 항목 조회

    확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
    따라서 user_id 필터 없이 check_item_id와 check_date만으로 확인.
    """
    today = date.today()

    # 사용자가 담당하는 시스템의 모든 체크 항목
    assignments = (
        db.query(UserSystemAssignment)
        .filter(UserSystemAssignment.user_id == current_user.id)
        .all()
    )

    system_ids = [a.system_id for a in assignments]
    all_items = db.query(CheckItem).filter(CheckItem.system_id.in_(system_ids)).all()

    # 오늘 체크된 항목 (다른 사람이 체크한 것도 포함)
    checked_records = (
        db.query(ChecklistRecord).filter(ChecklistRecord.check_date == today).all()
    )
    checked_item_ids = {r.check_item_id for r in checked_records}

    # 체크되지 않은 항목
    unchecked_items = [
        {
            "check_item_id": item.id,
            "item_name": item.item_name,
            "system_id": item.system_id,
            "system_name": db.query(System)
            .filter(System.id == item.system_id)
            .first()
            .system_name,
        }
        for item in all_items
        if item.id not in checked_item_ids
    ]

    return unchecked_items


@app.post("/api/console/export-excel")
async def export_excel(
    request: ExcelExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """체크리스트 통계 엑셀 다운로드"""
    check_console_access(current_user)
    
    # openpyxl import 확인
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.chart import BarChart, Reference
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"엑셀 생성 라이브러리(openpyxl)가 설치되지 않았습니다. pip install openpyxl (오류: {str(e)})",
        )
    
    try:
        
        # 날짜 범위 검증
        if request.start_date > request.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작 날짜가 종료 날짜보다 늦을 수 없습니다.",
            )
        
        # 날짜 범위 내의 모든 체크리스트 기록 조회
        records = (
            db.query(ChecklistRecord)
            .filter(
                and_(
                    ChecklistRecord.check_date >= request.start_date,
                    ChecklistRecord.check_date <= request.end_date,
                )
            )
            .all()
        )
        
        print(f"[엑셀 다운로드] 날짜 범위: {request.start_date} ~ {request.end_date}")
        print(f"[엑셀 다운로드] 조회된 기록 수: {len(records)}")
        
        # 모든 체크 항목 조회 (담당자 정보 포함)
        all_items = db.query(CheckItem).all()
        all_systems = db.query(System).all()
        all_assignments = db.query(UserSystemAssignment).all()
        all_users = db.query(User).all()
        
        print(f"[엑셀 다운로드] 전체 체크 항목 수: {len(all_items)}")
        print(f"[엑셀 다운로드] 전체 시스템 수: {len(all_systems)}")
        print(f"[엑셀 다운로드] 전체 담당자 할당 수: {len(all_assignments)}")
        
        # 시스템, 항목, 담당자 매핑 생성
        system_map = {s.id: s.system_name for s in all_systems}
        item_map = {item.id: item for item in all_items}
        
        # (system_id, item_name) 조합으로 담당자 매핑 생성
        assignment_map = {}
        for assignment in all_assignments:
            key = (assignment.system_id, assignment.item_name)
            if key not in assignment_map:
                assignment_map[key] = set()  # 중복 제거를 위해 set 사용
            user = next((u for u in all_users if u.id == assignment.user_id), None)
            if user:
                assignment_map[key].add(user.name)  # 사번 제거, 이름만 사용
        
        # set을 리스트로 변환 (정렬하여 일관성 유지)
        for key in assignment_map:
            assignment_map[key] = sorted(list(assignment_map[key]))
        
        user_map = {u.id: u.name for u in all_users}
        
        # 엑셀 워크북 생성
        wb = Workbook()
        ws = wb.active
        ws.title = "체크리스트 통계"
        
        # 스타일 정의
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        border_side = Side(style="thin", color="000000")
        border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # 헤더 작성
        headers = ["날짜", "시스템", "항목", "담당자", "상태", "비고"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_alignment
            cell.border = border
        
        # 데이터 작성 (중복 제거: 같은 check_item_id와 check_date에 대해 가장 최근 것만 사용)
        # 먼저 (check_item_id, check_date)별로 그룹화하고, 가장 최근 checked_at을 가진 레코드만 선택
        records_dict = {}
        for record in records:
            key = (record.check_item_id, record.check_date)
            if key not in records_dict:
                records_dict[key] = record
            else:
                # 같은 키가 있으면 checked_at이 더 최근인 것으로 교체
                if record.checked_at > records_dict[key].checked_at:
                    records_dict[key] = record
        
        # 실제로 기록이 있는 날짜만 추출
        dates_with_records = set()
        for record in records:
            dates_with_records.add(record.check_date)
        
        # 날짜 범위 내의 모든 날짜 생성 (실제 기록이 있는 날짜만)
        date_list = sorted(list(dates_with_records))
        
        # 실제 기록이 있는 날짜에 대해서만 데이터 생성
        excel_data = []
        for check_item in all_items:
            for check_date in date_list:
                key = (check_item.id, check_date)
                if key in records_dict:
                    # 체크된 기록이 있는 경우
                    record = records_dict[key]
                    excel_data.append({
                        'date': check_date,
                        'system_id': check_item.system_id,
                        'item_name': check_item.item_name,
                        'status': record.status,
                        'notes': record.notes or "",
                    })
                else:
                    # 해당 날짜에 체크되지 않은 항목 (미점검)
                    excel_data.append({
                        'date': check_date,
                        'system_id': check_item.system_id,
                        'item_name': check_item.item_name,
                        'status': '미점검',
                        'notes': "",
                    })
        
        # 날짜, 시스템, 항목 순으로 정렬
        excel_data.sort(key=lambda x: (x['date'], x['system_id'], x['item_name']))
        
        row_idx = 2
        for data in excel_data:
            system_name = system_map.get(data['system_id'], "")
            # (system_id, item_name) 조합으로 담당자 조회
            assignment_key = (data['system_id'], data['item_name'])
            responsible_users = ", ".join(assignment_map.get(assignment_key, []))
            
            ws.cell(row=row_idx, column=1, value=data['date'].strftime("%Y-%m-%d")).border = border
            ws.cell(row=row_idx, column=2, value=system_name).border = border
            ws.cell(row=row_idx, column=3, value=data['item_name']).border = border
            ws.cell(row=row_idx, column=4, value=responsible_users).border = border
            ws.cell(row=row_idx, column=5, value=data['status']).border = border
            ws.cell(row=row_idx, column=6, value=data['notes']).border = border
            
            row_idx += 1
        
        print(f"[엑셀 다운로드] 엑셀에 작성된 행 수: {row_idx - 2}")
        
        # 열 너비 조정
        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 25
        ws.column_dimensions["C"].width = 40
        ws.column_dimensions["D"].width = 30
        ws.column_dimensions["E"].width = 10
        ws.column_dimensions["F"].width = 50
        
        # 필터 적용
        ws.auto_filter.ref = f"A1:F{row_idx - 1}"
        
        # 통계 시트 생성
        stats_ws = wb.create_sheet("통계")
        
        # 날짜별 통계 계산
        date_stats = {}
        for record in records:
            date_str = record.check_date.strftime("%Y-%m-%d")
            if date_str not in date_stats:
                date_stats[date_str] = {"PASS": 0, "FAIL": 0, "UNCHECKED": 0}
            
            if record.status == "PASS":
                date_stats[date_str]["PASS"] += 1
            elif record.status == "FAIL":
                date_stats[date_str]["FAIL"] += 1
        
        # 전체 항목 수 계산
        total_items = len(all_items)
        
        # 통계 헤더
        stats_headers = ["날짜", "PASS", "FAIL", "미점검", "전체"]
        for col_idx, header in enumerate(stats_headers, 1):
            cell = stats_ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_alignment
            cell.border = border
        
        # 통계 데이터
        stats_row = 2
        sorted_dates = sorted(date_stats.keys())
        for date_str in sorted_dates:
            stats = date_stats[date_str]
            unchecked = total_items - stats["PASS"] - stats["FAIL"]
            
            stats_ws.cell(row=stats_row, column=1, value=date_str).border = border
            stats_ws.cell(row=stats_row, column=2, value=stats["PASS"]).border = border
            stats_ws.cell(row=stats_row, column=3, value=stats["FAIL"]).border = border
            stats_ws.cell(row=stats_row, column=4, value=unchecked).border = border
            stats_ws.cell(row=stats_row, column=5, value=total_items).border = border
            
            stats_row += 1
        
        # 통계 열 너비 조정
        stats_ws.column_dimensions["A"].width = 12
        stats_ws.column_dimensions["B"].width = 10
        stats_ws.column_dimensions["C"].width = 10
        stats_ws.column_dimensions["D"].width = 10
        stats_ws.column_dimensions["E"].width = 10
        
        # 차트 생성
        if len(sorted_dates) > 0:
            chart = BarChart()
            chart.type = "col"
            chart.style = 2
            chart.title = f"체크리스트 통계 ({request.start_date} ~ {request.end_date})"
            chart.y_axis.title = "개수"
            chart.x_axis.title = "날짜"
            
            data = Reference(stats_ws, min_col=2, min_row=1, max_col=4, max_row=stats_row - 1)
            cats = Reference(stats_ws, min_col=1, min_row=2, max_row=stats_row - 1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            
            stats_ws.add_chart(chart, "G2")
        
        # 메모리 버퍼에 엑셀 파일 저장
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # 파일명 생성 (한글 인코딩 처리)
        filename = f"체크리스트_통계_{request.start_date}_{request.end_date}.xlsx"
        # RFC 5987 형식으로 한글 파일명 인코딩
        from urllib.parse import quote
        encoded_filename = quote(filename.encode('utf-8'))
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            },
        )
    except Exception as e:
        # ImportError는 이미 함수 시작 부분에서 처리됨
        import traceback
        error_detail = traceback.format_exc()
        print(f"[엑셀 다운로드] 오류 발생: {str(e)}")
        print(f"[엑셀 다운로드] 상세 오류:\n{error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"엑셀 파일 생성 중 오류 발생: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
