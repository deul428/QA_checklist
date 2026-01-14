from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import date, datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from dotenv import load_dotenv

from services.database import SessionLocal
from models.models import User, CheckItem, ChecklistRecord, UserSystemAssignment, System

load_dotenv()

scheduler = BackgroundScheduler()

def get_korea_today():
    """한국 시간 기준 오늘 날짜 반환"""
    kst = pytz.timezone('Asia/Seoul')
    kst_now = datetime.now(kst)
    return kst_now.date()

def send_email(to_email: str, subject: str, body: str):
    """이메일 발송 함수"""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user).strip()
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    
    # ASCII가 아닌 문자 제거 (non-breaking space 등)
    smtp_user = smtp_user.encode('ascii', 'ignore').decode('ascii')
    smtp_password = smtp_password.encode('ascii', 'ignore').decode('ascii')
    smtp_from = smtp_from.encode('ascii', 'ignore').decode('ascii')
    
    if not smtp_user or not smtp_password:
        print("SMTP 설정이 없어 이메일을 발송할 수 없습니다")
        return
    
    # 디버깅 정보 출력
    print(f"SMTP 연결 정보:")
    print(f"  서버: {smtp_host}:{smtp_port}")
    print(f"  사용자: {smtp_user}")
    print(f"  발신자: {smtp_from}")
    print(f"  SSL 사용: {smtp_use_ssl}")
    
    try:
        msg = MIMEMultipart()
        # 발신자를 회사 도메인으로 설정 (Gmail SMTP 사용 시에도 회사 도메인으로 표시)
        # From 헤더에 이름과 이메일 주소 모두 포함
        from_name = os.getenv("SMTP_FROM_NAME", "QA 체크리스트 시스템").strip()
        msg['From'] = f"{from_name} <{smtp_from}>"
        msg['To'] = to_email
        # Reply-To를 회사 도메인으로 설정 (회신 시 회사 도메인으로 보내짐)
        msg['Reply-To'] = smtp_from
        # 제목을 UTF-8로 인코딩
        msg['Subject'] = str(Header(subject, 'utf-8'))
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # SSL 사용 여부에 따라 다른 방식으로 연결
        if smtp_use_ssl:
            # SSL 사용 (포트 465 등)
            import ssl
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
        else:
            # TLS 사용 (포트 587 등)
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"이메일 발송 완료: {to_email}")
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        import traceback
        traceback.print_exc()

def check_unchecked_items():
    """미체크 항목 확인 및 메일 발송
    
    한국 시간 기준으로 오늘 날짜를 사용하여 미체크 항목을 확인하고
    담당자들에게 이메일을 발송합니다.
    """
    db: Session = SessionLocal()
    try:
        # 한국 시간 기준 오늘 날짜 사용
        today = get_korea_today()
        print(f"[스케줄러] 한국 시간 기준 오늘 날짜: {today}")
        
        # 모든 사용자 조회
        users = db.query(User).all()
        
        for user in users:
            # 사용자가 담당하는 시스템의 모든 체크 항목
            assignments = db.query(UserSystemAssignment).filter(
                UserSystemAssignment.user_id == user.id
            ).all()
            
            if not assignments:
                continue
            
            system_ids = [a.system_id for a in assignments]
            all_items = db.query(CheckItem).filter(CheckItem.system_id.in_(system_ids)).all()
            
            # 오늘 체크된 항목 (다른 사람이 체크한 것도 포함)
            # 확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
            checked_records = db.query(ChecklistRecord).filter(
                ChecklistRecord.check_date == today
            ).all()
            checked_item_ids = {r.check_item_id for r in checked_records}
            
            # 체크되지 않은 항목
            unchecked_items = [
                item for item in all_items
                if item.id not in checked_item_ids
            ]
            
            if unchecked_items:
                # 시스템별로 그룹화
                system_items = {}
                for item in unchecked_items:
                    system = db.query(System).filter(System.id == item.system_id).first()
                    if system:
                        if system.system_name not in system_items:
                            system_items[system.system_name] = []
                        system_items[system.system_name].append(item.item_name)
                
                # 이메일 본문 생성
                email_body = f"""
                <html>
                <body>
                    <h2>QA 체크리스트 미체크 항목 알림</h2>
                    <p>안녕하세요, {user.name}님</p>
                    <p>오늘({today}) 체크되지 않은 항목이 있습니다. 확인 부탁드립니다.</p>
                    <ul>
                """
                
                for system_name, items in system_items.items():
                    email_body += f"<li><strong>{system_name}</strong><ul>"
                    for item_name in items:
                        email_body += f"<li>{item_name}</li>"
                    email_body += "</ul></li>"
                
                email_body += """
                    </ul>
                    <p>시스템에 로그인하여 체크리스트를 완료해주세요.</p>
                </body>
                </html>
                """
                
                subject = f"[QA 체크리스트] 미체크 항목 알림 - {today}"
                send_email(user.email, subject, email_body)
        
    except Exception as e:
        print(f"미체크 항목 확인 중 오류 발생: {e}")
    finally:
        db.close()

def init_scheduler():
    """스케줄러 초기화 및 작업 등록"""
    if scheduler.running:
        return
    
    # 한국 시간 기준 09:00, 12:00에 실행
    scheduler.add_job(
        check_unchecked_items,
        trigger=CronTrigger(hour=9, minute=0, timezone='Asia/Seoul'),
        id='check_morning',
        name='오전 9시 체크리스트 확인',
        replace_existing=True
    )
    
    scheduler.add_job(
        check_unchecked_items,
        trigger=CronTrigger(hour=12, minute=0, timezone='Asia/Seoul'),
        id='check_noon',
        name='오후 12시 체크리스트 확인',
        replace_existing=True
    )
    
    scheduler.start()
    print("스케줄러가 시작되었습니다. 매일 09:00, 12:00에 미체크 항목을 확인합니다.")

