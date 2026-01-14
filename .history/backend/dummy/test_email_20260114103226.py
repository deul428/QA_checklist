"""
메일 발송 테스트 스크립트
실행: python test_email.py
"""
import os
from dotenv import load_dotenv
from scheduler import send_email
from datetime import date

load_dotenv()

def test_email():
    """kimhs@ajnet.co.kr로 테스트 메일 발송"""
    
    # SMTP 설정 확인
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    print("=" * 50)
    print("메일 발송 테스트")
    print("=" * 50)
    print(f"SMTP_USER: {smtp_user if smtp_user else '[설정되지 않음]'}")
    print(f"SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else '[설정되지 않음]'}")
    print()
    
    if not smtp_user or not smtp_password:
        print("[오류] SMTP 설정이 없습니다!")
        print("   .env 파일에 다음 설정을 추가하세요:")
        print()
        print("   SMTP_HOST=smtp.gmail.com")
        print("   SMTP_PORT=587")
        print("   SMTP_USER=your-gmail@gmail.com")
        print("   SMTP_PASSWORD=앱_비밀번호")
        print("   SMTP_FROM_EMAIL=회사_이메일@ajnet.co.kr")
        print("   SMTP_USE_SSL=false")
        return
    
    # 테스트 메일 내용
    test_email_address = "kimhs@ajnet.co.kr"
    today = date.today()
    
    subject = f"[QA 체크리스트] 메일 발송 테스트 - {today}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">QA 체크리스트 시스템 메일 발송 테스트</h2>
            <p>안녕하세요,</p>
            <p>이 메일은 QA 체크리스트 시스템의 메일 발송 기능 테스트입니다.</p>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>테스트 정보:</strong></p>
                <ul>
                    <li>발송 시간: {today}</li>
                    <li>수신자: {test_email_address}</li>
                    <li>상태: 테스트 메일</li>
                </ul>
            </div>
            <p>이 메일이 정상적으로 수신되었다면 메일 발송 기능이 정상적으로 작동하는 것입니다.</p>
        </div>
    </body>
    </html>
    """
    
    print(f"테스트 메일 발송 중...")
    print(f"  수신자: {test_email_address}")
    print(f"  제목: {subject}")
    print()
    
    try:
        send_email(test_email_address, subject, body)
        print()
        print("=" * 50)
        print("[완료] 테스트 메일 발송 완료!")
        print("=" * 50)
        print(f"수신함({test_email_address})을 확인해주세요.")
    except Exception as e:
        print()
        print("=" * 50)
        print("[오류] 메일 발송 실패!")
        print("=" * 50)
        print(f"오류: {e}")

if __name__ == "__main__":
    test_email()

