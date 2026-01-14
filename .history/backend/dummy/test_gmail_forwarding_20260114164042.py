"""
Gmail SMTP를 사용하여 회사 도메인으로 메일 발송 테스트
실행: python test_gmail_forwarding.py
"""
import os
from dotenv import load_dotenv
from scheduler import send_email
from datetime import date

load_dotenv()

def test_gmail_forwarding():
    """Gmail SMTP를 통한 회사 도메인 메일 발송 테스트"""
    
    # SMTP 설정 확인
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM_EMAIL")
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "DX본부 시스템 체크리스트")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    
    print("=" * 60)
    print("Gmail → 회사 도메인 메일 발송 테스트")
    print("=" * 60)
    print(f"Gmail 계정: {smtp_user if smtp_user else '[설정되지 않음]'}")
    print(f"발신자 이메일: {smtp_from if smtp_from else '[설정되지 않음]'}")
    print(f"발신자 이름: {smtp_from_name}")
    print(f"SMTP 서버: {smtp_host}")
    print()
    
    if not smtp_user or not smtp_password or not smtp_from:
        print("[오류] SMTP 설정이 없습니다!")
        print()
        print(".env 파일에 다음 설정을 추가하세요:")
        print()
        print("SMTP_HOST=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USER=your-gmail@gmail.com")
        print("SMTP_PASSWORD=앱_비밀번호_16자리")
        print("SMTP_FROM_EMAIL=회사_이메일@ajnet.co.kr")
        print("SMTP_FROM_NAME=DX본부 시스템 체크리스트")
        print("SMTP_USE_SSL=false")
        return
    
    # 테스트 메일 내용
    test_email_address = "kimhs@ajnet.co.kr"
    today = date.today()
    
    subject = f"[QA 체크리스트] Gmail 포워딩 테스트 - {today}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">DX본부 시스템 체크리스트 메일 발송 테스트</h2>
            <p>안녕하세요,</p>
            <p>이 메일은 Gmail SMTP를 통해 발송되었으며, 발신자가 회사 도메인으로 설정되어 있습니다.</p>
        </div>
    </body>
    </html>
    """
    
    print(f"테스트 메일 발송 중...")
    print(f"  수신자: {test_email_address}")
    print(f"  발신자: {smtp_from_name} <{smtp_from}>")
    print(f"  제목: {subject}")
    print()
    
    try:
        send_email(test_email_address, subject, body)
        print()
        print("=" * 60)
        print("[완료] 테스트 메일 발송 완료!")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print("[오류] 메일 발송 실패!")
        print("=" * 60)
        print(f"오류: {e}")

if __name__ == "__main__":
    test_gmail_forwarding()

