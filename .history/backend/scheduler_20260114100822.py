from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from dotenv import load_dotenv

from database import SessionLocal
from models import User, CheckItem, ChecklistRecord, UserSystemAssignment, System

load_dotenv()

scheduler = BackgroundScheduler()

def send_email(to_email: str, subject: str, body: str):
    """이메일 발송 함수"""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user).strip()
    
    # ASCII가 아닌 문자 제거 (non-breaking space 등)
    smtp_user = smtp_user.encode('ascii', 'ignore').decode('ascii')
    smtp_password = smtp_password.encode('ascii', 'ignore').decode('ascii')
    smtp_from = smtp_from.encode('ascii', 'ignore').decode('ascii')
    
    if not smtp_user or not smtp_password:
        print("SMTP 설정이 없어 이메일을 발송할 수 없습니다")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = to_email
        # 제목을 UTF-8로 인코딩
        msg['Subject'] = str(Header(subject, 'utf-8'))
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
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
    """미체크 항목 확인 및 메일 발송"""
    db: Session = SessionLocal()
    try:
        today = date.today()
        
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
            
            # 오늘 체크된 항목
            checked_records = db.query(ChecklistRecord).filter(
                ChecklistRecord.user_id == user.id,
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

