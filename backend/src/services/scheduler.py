from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
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
    kst = pytz.timezone("Asia/Seoul")
    kst_now = datetime.now(kst)
    return kst_now.date()


def send_email(to_email: str, subject: str, body: str, cc_emails: list = None):
    """이메일 발송 함수

    Args:
        to_email: 수신자 이메일 주소
        subject: 이메일 제목
        body: 이메일 본문 (HTML)
        cc_emails: CC 받을 이메일 주소 리스트 (선택사항)
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user).strip()
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

    # 환경 변수에서 CC 이메일 읽기 (쉼표로 구분된 여러 이메일 지원)
    if cc_emails is None:
        cc_env = os.getenv("SMTP_CC_EMAILS", "").strip()
        if cc_env:
            cc_emails = [email.strip() for email in cc_env.split(",") if email.strip()]
        else:
            cc_emails = []

    # ASCII가 아닌 문자 제거 (non-breaking space 등)
    smtp_user = smtp_user.encode("ascii", "ignore").decode("ascii")
    smtp_password = smtp_password.encode("ascii", "ignore").decode("ascii")
    smtp_from = smtp_from.encode("ascii", "ignore").decode("ascii")

    if not smtp_user or not smtp_password:
        print("SMTP 설정이 없어 이메일을 발송할 수 없습니다")
        return

    # 디버깅 정보 출력 (간소화)
    cc_info = f", CC: {len(cc_emails)}명" if cc_emails else ""
    print(f"[메일 발송] {smtp_user} → {to_email}{cc_info}")

    try:
        msg = MIMEMultipart()
        # 발신자를 회사 도메인으로 설정 (Gmail SMTP 사용 시에도 회사 도메인으로 표시)
        # From 헤더에 이름과 이메일 주소 모두 포함
        from_name = os.getenv("SMTP_FROM_NAME", "DX본부 시스템 체크리스트").strip()
        msg["From"] = f"{from_name} <{smtp_from}>"
        msg["To"] = to_email
        # CC 설정
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        # Reply-To를 회사 도메인으로 설정 (회신 시 회사 도메인으로 보내짐)
        msg["Reply-To"] = smtp_from
        # 제목을 UTF-8로 인코딩
        msg["Subject"] = str(Header(subject, "utf-8"))
        msg.attach(MIMEText(body, "html", "utf-8"))

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
        # 수신자와 CC를 모두 포함하여 발송
        recipients = [to_email]
        if cc_emails:
            recipients.extend(cc_emails)
        
        # 메일 발송 (실제 발송 여부 확인)
        try:
            result = server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            # 발송 결과 확인
            if result:
                failed_recipients = result
                if failed_recipients:
                    print(f"이메일 발송 실패: 일부 수신자에게 발송 실패")
                    print(f"  실패한 수신자: {failed_recipients}")
                else:
                    cc_info = f" (CC: {len(cc_emails)}명)" if cc_emails else ""
                    print(f"✓ 이메일 발송 성공: {to_email}{cc_info}")
            else:
                cc_info = f" (CC: {len(cc_emails)}명)" if cc_emails else ""
                print(f"✓ 이메일 발송 성공: {to_email}{cc_info}")
        except Exception as send_error:
            server.quit()
            raise send_error
    except smtplib.SMTPAuthenticationError as e:
        print(f"이메일 발송 실패: SMTP 인증 오류")
        print(f"  오류 코드: {e.smtp_code}")
        print(f"  오류 메시지: {e.smtp_error.decode('utf-8') if isinstance(e.smtp_error, bytes) else e.smtp_error}")
        if "gmail.com" in smtp_host.lower():
            print("\n[Gmail 인증 문제 해결 방법]")
            print("1. Gmail 계정에서 2단계 인증이 활성화되어 있는지 확인하세요.")
            print("2. Google 계정 설정 > 보안 > 2단계 인증 > 앱 비밀번호에서 앱 비밀번호를 생성하세요.")
            print("3. 생성된 앱 비밀번호를 .env 파일의 SMTP_PASSWORD에 설정하세요.")
            print("4. 일반 비밀번호가 아닌 앱 비밀번호를 사용해야 합니다.")
        import traceback
        traceback.print_exc()
    except smtplib.SMTPDataError as e:
        error_msg = e.smtp_error.decode('utf-8') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        print(f"이메일 발송 실패: SMTP 데이터 오류")
        print(f"  오류 코드: {e.smtp_code}")
        print(f"  오류 메시지: {error_msg}")
        if "gmail.com" in smtp_host.lower() and "Daily user sending limit" in error_msg:
            print("\n[Gmail 일일 발송 한도 초과 문제 해결 방법]")
            print("Gmail 무료 계정은 하루에 약 500개의 이메일만 보낼 수 있습니다.")
            print("해결 방법:")
            print("1. 24시간 후에 다시 시도하세요.")
            print("2. Gmail Workspace(구 G Suite) 계정을 사용하면 더 높은 한도가 있습니다.")
            print("3. 여러 수신자에게 보낼 때는 BCC를 사용하거나, 수신자를 그룹으로 묶어서 보내세요.")
            print("4. 회사 이메일 서버(SMTP)를 사용하는 것을 권장합니다.")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        import traceback

        traceback.print_exc()


def check_unchecked_items():
    """미체크 항목 확인 및 통합 메일 발송

    한국 시간 기준으로 오늘 날짜를 사용하여 미체크 항목을 확인하고
    모든 담당자에게 통합된 하나의 메일을 발송합니다.

    테스트 모드: .env 파일에 SCHEDULER_TEST_EMAIL이 설정되어 있으면
    해당 이메일로만 발송합니다.
    """
    db: Session = SessionLocal()
    try:
        # 한국 시간 기준 오늘 날짜 사용
        today = get_korea_today()
        print(f"[스케줄러] 한국 시간 기준 오늘 날짜: {today}")

        # 테스트 모드 확인
        test_email = os.getenv("SCHEDULER_TEST_EMAIL", "").strip()
        is_test_mode = bool(test_email)

        if is_test_mode:
            print(
                f"[스케줄러] 테스트 모드 활성화 - 모든 이메일을 {test_email}로 발송합니다"
            )

        # 오늘 체크된 항목 (다른 사람이 체크한 것도 포함)
        # 확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
        checked_records = (
            db.query(ChecklistRecord).filter(ChecklistRecord.check_date == today).all()
        )
        checked_item_ids = {(r.check_item_id, r.environment) for r in checked_records}

        # 모든 체크 항목 조회
        all_check_items = db.query(CheckItem).filter(CheckItem.status == "active").all()

        # 체크되지 않은 항목 필터링 (환경별로 구분)
        unchecked_items = [
            item for item in all_check_items 
            if (item.item_id, item.environment) not in checked_item_ids
        ]

        if not unchecked_items:
            print(f"[스케줄러] 오늘 체크되지 않은 항목이 없습니다.")
            return

        # 미체크 항목의 담당자 수집
        responsible_users = set()
        system_items = {}  # {system_name: set(item_name, ...)} - 항목명 기준 중복 제거

        for item in unchecked_items:
            # 해당 항목의 담당자 조회 (환경 무관하게 배정 확인)
            assignments = (
                db.query(UserSystemAssignment)
                .filter(
                    UserSystemAssignment.system_id == item.system_id,
                    UserSystemAssignment.item_id == item.item_id,
                )
                .all()
            )

            # 담당자 정보 수집 (메일 발송용, 메일 본문에는 표시하지 않음)
            for assignment in assignments:
                user = db.query(User).filter(User.user_id == assignment.user_id).first()
                if user:
                    responsible_users.add(user)

            # 시스템별로 그룹화 (환경 무관하게 항목명 기준 중복 제거)
            system = db.query(System).filter(System.system_id == item.system_id).first()
            if system:
                system_name = system.system_name
                # 시스템명만 키로 사용 (환경 구분 없이, 같은 시스템 내에서 항목명 중복 제거)
                if system_name not in system_items:
                    system_items[system_name] = set()  # 중복 제거를 위해 set 사용
                # 항목 이름만 저장 (담당자 정보 제외, 중복 제거)
                system_items[system_name].add(item.item_name.strip())

        if not responsible_users:
            print(f"[스케줄러] 미체크 항목의 담당자가 없습니다.")
            return

        subject = f"[요청] 시스템 체크리스트 미점검 항목 확인 요청 ({today})"

        # 수신인: 미점검 담당자 모두
        recipient_emails = []
        recipient_names = []
        if is_test_mode:
            recipient_emails = [test_email]
            recipient_names = ["테스트 이메일"]
            print(f"  [테스트 모드] 통합 메일을 {test_email}로 발송합니다")
        else:
            recipient_emails = [user.user_email for user in responsible_users if user.user_email]
            recipient_names = [user.user_name for user in responsible_users if user.user_email]
            print(
                f"  [스케줄러] 통합 메일을 {len(recipient_emails)}명의 담당자에게 발송합니다"
            )
            print(
                f"    수신인: {', '.join([f'{name}({email})' for name, email in zip(recipient_names, recipient_emails)])}"
            )

        # 참조: 담당자들의 팀장 및 DX본부 본부장
        cc_emails = []
        cc_names = []
        if not is_test_mode:
            # 담당자들의 총괄본부 정보 수집 (팀장 찾기용)
            responsible_general_headquarters = set()
            for user in responsible_users:
                if user.general_headquarters:
                    responsible_general_headquarters.add(user.general_headquarters)

            # 팀장 찾기: 담당자와 같은 general_headquarters를 가진 팀장
            # 팀장은 division과 general_headquarters만 존재
            all_team_leaders = (
                db.query(User)
                .filter(
                    ((User.position == "팀장") | (User.role == "팀장"))
                    & User.user_email.isnot(None)
                )
                .all()
            )

            # 담당자와 같은 general_headquarters를 가진 팀장 필터링
            if responsible_general_headquarters:
                filtered_team_leaders = []
                for tl in all_team_leaders:
                    if (
                        tl.general_headquarters
                        and tl.general_headquarters in responsible_general_headquarters
                    ):
                        filtered_team_leaders.append(tl)
                team_leaders = filtered_team_leaders
                print(
                    f"    [참조] 담당자의 총괄본부: {responsible_general_headquarters}"
                )
                print(f"    [참조] 매칭된 팀장: {len(team_leaders)}명")
            else:
                # 담당자의 총괄본부 정보가 없으면 모든 팀장 포함
                print(
                    f"    [참고] 담당자의 총괄본부 정보가 없어 모든 팀장을 참조자로 추가합니다."
                )
                team_leaders = all_team_leaders

            # DX본부 본부장 찾기: division에 DX가 포함된 본부장
            # 본부장은 division만 존재
            dx_directors = (
                db.query(User)
                .filter(
                    ((User.position == "본부장") | (User.role == "본부장"))
                    & (User.division.like("%DX%"))
                    & User.user_email.isnot(None)
                )
                .all()
            )

            # 참조자 수집: 담당자들의 팀장 + DX본부 본부장
            # 이메일 중복 체크 없이 단순히 팀장과 본부장을 참조자로 추가
            cc_emails = []
            cc_names = []

            # 담당자들의 팀장 추가 (같은 총괄본부의 팀장)
            for tl in team_leaders:
                if tl.user_email:
                    cc_emails.append(tl.user_email)
                    cc_names.append(tl.user_name)

            # DX본부 본부장 추가 (무조건 참조자로 포함, 이메일 중복 무시)
            for director in dx_directors:
                if director.user_email:
                    # 본부장은 무조건 참조자로 포함 (팀장과 같은 이메일이어도 포함)
                    cc_emails.append(director.user_email)
                    cc_names.append(director.user_name)
                    print(f"    [참조] 본부장 추가: {director.user_name} ({director.user_email})")

            print(
                f"  [스케줄러] CC: {len(cc_emails)}명 (팀장 {len(team_leaders)}명, DX본부 본부장 {len(dx_directors)}명)"
            )
            if cc_emails:
                print(
                    f"    참조: {', '.join([f'{name}({email})' for name, email in zip(cc_names, cc_emails)])}"
                )

        # 수신인 및 참조자 정보 (메일 본문용)
        recipient_info = ""
        cc_info = ""
        # if not is_test_mode:
        # if recipient_names:
        #     recipient_info = f"<p style='color: #666; font-size: 11px; margin-bottom: 10px;'><strong>수신인:</strong> {', '.join(recipient_names)}</p>"
        # # 참조자 정보는 cc_names가 있을 때만 생성
        # if cc_names:
        #     cc_info = f"<p style='color: #666; font-size: 11px; margin-bottom: 10px;'><strong>참조:</strong> {', '.join(cc_names)}</p>"
        #     print(f"    [디버깅] 메일 본문에 참조자 정보 추가: {len(cc_names)}명")
        # else:
        #     # 디버깅: 참조자가 없는 경우 로그 출력
        #     print(f"    [디버깅] 참조자가 없어 메일 본문에 참조자 정보를 표시하지 않습니다. (cc_emails={len(cc_emails)}, cc_names={len(cc_names)})")

        # 통합 이메일 본문 생성
        email_body = f"""
            <html>
                <body>
                    <h3>시스템 체크리스트 미체크 항목 알림</h3> 
                    <p style="color: #d10000; font-size: 12px; font-weight:bold;">&#8251; 해당 메일은 시스템 체크리스트 미수행 담당자에게 발송하는 건입니다.</p>
                    {recipient_info if recipient_info else ''}
                    {cc_info if cc_info else ''}
                    <p>안녕하세요. DX본부 시스템 체크리스트 안내입니다.</p> 
                    <br />
                    <p>주요 기능의 장애 예방을 위해 본 메일 수신 시 각 담당자분들께서는 미점검 상태로 남아 있는 시스템 체크리스트 항목을 확인하여 작성 부탁드립니다.</p>
                    <br />
                    <p style="margin-bottom: 40px;">또한 정/부 담당자 모두 부재 예정인 경우에는, 점검이 누락되지 않도록 사전에 대체 담당자를 지정하여 점검을 진행해 주시기 바랍니다.</p>
                    <h3>[미점검 항목]</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border: 1px solid #ddd; font-size: 14px; font-weight: bold;">시스템</th>
                                <th style="padding: 10px; text-align: left; border: 1px solid #ddd; font-size: 14px; font-weight: bold;">항목</th>
                            </tr>
                        </thead>
                        <tbody>
            """
        for system_name, items_set in system_items.items():
            # set을 정렬된 리스트로 변환
            items = sorted(list(items_set))
            for idx, item_name in enumerate(items):
                if idx == 0:
                    # 첫 번째 항목: 시스템명과 항목명 모두 표시
                    email_body += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 14px; font-weight: bold; vertical-align: top;" rowspan="{len(items)}">{system_name}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 14px;">{item_name}</td>
                            </tr>
                    """
                else:
                    # 두 번째 항목부터: 항목명만 표시
                    email_body += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 14px;">{item_name}</td>
                            </tr>
                    """

        email_body += """
                        </tbody>
                    </table>
                    <br> 
            <p>바쁘신 와중에 협조해 주셔서 감사합니다.</p> 
            <p style="color: #888; font-size: 12px; margin-top: 20px;">시스템 장애/오류 문의: QA혁신팀 김희수 사원</p> 
        </body>
        </html>
        """

        if recipient_emails:
            # 첫 번째 담당자 이메일을 To로, 나머지 담당자는 CC에 추가
            to_email = recipient_emails[0]
            # 나머지 담당자도 CC에 추가
            remaining_recipients = (
                recipient_emails[1:] if len(recipient_emails) > 1 else []
            )
            all_cc_emails = list(set(remaining_recipients + cc_emails))  # 중복 제거

            send_email(to_email, subject, email_body, cc_emails=all_cc_emails)

    except Exception as e:
        print(f"미체크 항목 확인 중 오류 발생: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def send_test_email_scheduled():
    """스케줄된 테스트 메일 발송 함수

    실제 DB에서 미체크 항목을 읽어서 실제 메일과 동일한 형식으로 발송합니다.
    """
    db: Session = SessionLocal()
    try:
        # 한국 시간 기준 오늘 날짜 사용
        today = get_korea_today()
        kst = pytz.timezone("Asia/Seoul")
        now = datetime.now(kst)

        print(f"[테스트 메일] 한국 시간 기준 오늘 날짜: {today}")

        # 오늘 체크된 항목 (다른 사람이 체크한 것도 포함)
        # 확인자가 여러 명인 경우, 한 명이 체크하면 다른 사람도 체크된 것으로 보임.
        checked_records = (
            db.query(ChecklistRecord).filter(ChecklistRecord.check_date == today).all()
        )
        checked_item_ids = {(r.check_item_id, r.environment) for r in checked_records}

        # 모든 체크 항목 조회
        all_check_items = db.query(CheckItem).filter(CheckItem.status == "active").all()

        # 체크되지 않은 항목 필터링 (환경별로 구분)
        unchecked_items = [
            item for item in all_check_items 
            if (item.item_id, item.environment) not in checked_item_ids
        ]

        if not unchecked_items:
            print(f"[테스트 메일] 오늘 체크되지 않은 항목이 없습니다.")
            return
        else:
            # 미체크 항목의 담당자 수집
            responsible_users = set()
            system_items = {}  # {system_name: set(item_name, ...)} - 항목명 기준 중복 제거

            for item in unchecked_items:
                # 해당 항목의 담당자 조회 (환경 무관하게 배정 확인)
                assignments = (
                    db.query(UserSystemAssignment)
                    .filter(
                        UserSystemAssignment.system_id == item.system_id,
                        UserSystemAssignment.item_id == item.item_id,
                    )
                    .all()
                )

                # 담당자 정보 수집 (메일 발송용, 메일 본문에는 표시하지 않음)
                for assignment in assignments:
                    user = db.query(User).filter(User.user_id == assignment.user_id).first()
                    if user:
                        responsible_users.add(user)

                # 시스템별로 그룹화 (환경 무관하게 항목명 기준 중복 제거)
                system = db.query(System).filter(System.system_id == item.system_id).first()
                if system:
                    system_name = system.system_name
                    # 시스템명만 키로 사용 (환경 구분 없이, 같은 시스템 내에서 항목명 중복 제거)
                    if system_name not in system_items:
                        system_items[system_name] = set()  # 중복 제거를 위해 set 사용
                    # 항목 이름만 저장 (담당자 정보 제외, 중복 제거)
                    system_items[system_name].add(item.item_name.strip())

        subject = f"[요청] 시스템 체크리스트 미점검 항목 확인 요청 ({today})"

        # 실제 담당자 이메일 주소 사용
        if not responsible_users:
            print(f"[테스트 메일] 미체크 항목의 담당자가 없습니다.")
            return

        # 수신인: 미점검 담당자 모두
        recipient_emails = [user.user_email for user in responsible_users if user.user_email]

        if not recipient_emails:
            print(f"[테스트 메일] 담당자의 이메일 주소가 없습니다.")
            return

        # 수신인 이름 수집
        recipient_names = [user.user_name for user in responsible_users if user.user_email]

        print(
            f"[테스트 메일] 통합 메일을 {len(recipient_emails)}명의 담당자에게 발송합니다"
        )
        print(
            f"  수신인: {', '.join([f'{name}({email})' for name, email in zip(recipient_names, recipient_emails)])}"
        )

        # 참조: 담당자들의 팀장 및 DX본부 본부장
        # 담당자들의 총괄본부 정보 수집 (팀장 찾기용)
        responsible_general_headquarters = set()
        for user in responsible_users:
            if user.general_headquarters:
                responsible_general_headquarters.add(user.general_headquarters)

        # 팀장 찾기: 담당자와 같은 general_headquarters를 가진 팀장
        # 팀장은 division과 general_headquarters만 존재
        all_team_leaders = (
            db.query(User)
            .filter(
                ((User.position == "팀장") | (User.role == "팀장"))
                & User.user_email.isnot(None)
            )
            .all()
        )

        # 담당자와 같은 general_headquarters를 가진 팀장 필터링
        if responsible_general_headquarters:
            filtered_team_leaders = []
            for tl in all_team_leaders:
                if (
                    tl.general_headquarters
                    and tl.general_headquarters in responsible_general_headquarters
                ):
                    filtered_team_leaders.append(tl)
            team_leaders = filtered_team_leaders
            print(f"    [참조] 담당자의 총괄본부: {responsible_general_headquarters}")
            print(f"    [참조] 매칭된 팀장: {len(team_leaders)}명")
        else:
            # 담당자의 총괄본부 정보가 없으면 모든 팀장 포함
            print(
                f"    [참고] 담당자의 총괄본부 정보가 없어 모든 팀장을 참조자로 추가합니다."
            )
            team_leaders = all_team_leaders

        # DX본부 본부장 찾기: division에 DX가 포함된 본부장
        # 본부장은 division만 존재
        dx_directors = (
            db.query(User)
            .filter(
                ((User.position == "본부장") | (User.role == "본부장"))
                & (User.division.like("%DX%"))
                & User.user_email.isnot(None)
            )
            .all()
        )

        # 참조자 수집: 담당자들의 팀장 + DX본부 본부장
        # 이메일 중복 체크 없이 단순히 팀장과 본부장을 참조자로 추가
        cc_emails = []
        cc_names = []

        # 담당자들의 팀장 추가 (같은 총괄본부의 팀장)
        for tl in team_leaders:
            if tl.user_email:
                cc_emails.append(tl.user_email)
                cc_names.append(tl.user_name)

        # DX본부 본부장 추가 (무조건 참조자로 포함, 이메일 중복 무시)
        for director in dx_directors:
            if director.user_email:
                # 본부장은 무조건 참조자로 포함 (팀장과 같은 이메일이어도 포함)
                cc_emails.append(director.user_email)
                cc_names.append(director.user_name)
                print(f"    [참조] 본부장 추가: {director.user_name} ({director.user_email})")

        print(
            f"[테스트 메일] CC: {len(cc_emails)}명 (팀장 {len(team_leaders)}명, DX본부 본부장 {len(dx_directors)}명)"
        )
        if cc_emails:
            print(
                f"  참조: {', '.join([f'{name}({email})' for name, email in zip(cc_names, cc_emails)])}"
            )

        # 수신인 및 참조자 정보 (메일 본문용)
        recipient_info = f"<p style='color: #666; font-size: 11px; margin-bottom: 10px;'><strong>수신인:</strong> {', '.join(recipient_names)}</p>"
        cc_info = ""
        if cc_names:
            cc_info = f"<p style='color: #666; font-size: 11px; margin-bottom: 10px;'><strong>참조:</strong> {', '.join(cc_names)}</p>"
        else:
            # 디버깅: 참조자가 없는 경우 로그 출력
            print(
                f"    [참고] 참조자가 없어 메일 본문에 참조자 정보를 표시하지 않습니다."
            )

        # 실제 메일과 동일한 형식의 이메일 본문 생성
        email_body = f"""
            <html>
                <body>
                    <h3>시스템 체크리스트 미체크 항목 알림</h3> 
                    <p style="color: #d10000; font-size: 12px; font-weight:bold;">&#8251; 해당 메일은 시스템 체크리스트 미수행 담당자에게 발송하는 건입니다.</p>
                    {recipient_info}
                    {cc_info}
                    <p>안녕하세요. DX본부 시스템 체크리스트 안내입니다.</p> 
                    <br />
                    <p>주요 기능의 장애 예방을 위해 본 메일 수신 시 각 담당자분들께서는 미점검 상태로 남아 있는 시스템 체크리스트 항목을 확인하여 작성 부탁드립니다.</p>
                    <br />
                    <p style="margin-bottom: 40px;">또한 정/부 담당자 모두 부재 예정인 경우에는, 점검이 누락되지 않도록 사전에 대체 담당자를 지정하여 점검을 진행해 주시기 바랍니다.</p>
                    <h3>[미점검 항목]</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; border: 1px solid #ddd; font-size: 14px; font-weight: bold;">시스템</th>
                                <th style="padding: 10px; text-align: left; border: 1px solid #ddd; font-size: 14px; font-weight: bold;">항목</th>
                            </tr>
                        </thead>
                        <tbody>
            """

        for system_name, items_set in system_items.items():
            # set을 정렬된 리스트로 변환
            items = sorted(list(items_set))
            for idx, item_name in enumerate(items):
                if idx == 0:
                    # 첫 번째 항목: 시스템명과 항목명 모두 표시
                    email_body += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 14px; font-weight: bold; vertical-align: top;" rowspan="{len(items)}">{system_name}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 14px;">{item_name}</td>
                            </tr>
                    """
                else:
                    # 두 번째 항목부터: 항목명만 표시
                    email_body += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 14px;">{item_name}</td>
                            </tr>
                    """

        email_body += """
                        </tbody>
                    </table>
                    <br>
            <p>바쁘신 와중에 협조해 주셔서 감사합니다.</p> 
            <p style="color: #888; font-size: 12px; margin-top: 20px;">시스템 장애/오류 문의: QA혁신팀 김희수 사원</p>
        </body>
        </html>
        """

        # 첫 번째 담당자 이메일을 To로, 나머지 담당자와 팀장/본부장은 CC로 설정
        to_email = recipient_emails[0]
        remaining_recipients = recipient_emails[1:] if len(recipient_emails) > 1 else []
        all_cc_emails = list(set(remaining_recipients + cc_emails))  # 중복 제거

        send_email(
            to_email=to_email,
            subject=subject,
            body=email_body,
            cc_emails=all_cc_emails,
        )

    except Exception as e:
        print(f"[테스트 메일] 오류 발생: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def schedule_test_email(hour: int, minute: int):
    """테스트 메일을 지정된 시간에 발송하도록 스케줄링

    Args:
        hour: 시 (0-23)
        minute: 분 (0-59)

    Returns:
        str: 스케줄된 작업 ID
    """
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    today = now.date()

    # 오늘 날짜의 지정된 시간으로 datetime 생성
    scheduled_time = kst.localize(
        datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
    )

    # 이미 지난 시간이면 내일로 설정
    if scheduled_time <= now:
        scheduled_time = scheduled_time + timedelta(days=1)

    # 고유한 작업 ID 생성
    job_id = f"test_email_{scheduled_time.strftime('%Y%m%d_%H%M')}"

    # 기존 작업이 있으면 제거
    try:
        scheduler.remove_job(job_id)
    except:
        pass

    # 새 작업 추가
    scheduler.add_job(
        send_test_email_scheduled,
        trigger=DateTrigger(run_date=scheduled_time),
        id=job_id,
        name=f"테스트 메일 발송 - {scheduled_time.strftime('%Y-%m-%d %H:%M')}",
        replace_existing=True,
    )

    return job_id, scheduled_time


def init_scheduler():
    """스케줄러 초기화 및 작업 등록"""
    if scheduler.running:
        return

    # .env에서 스케줄 시간 읽기 (기본값: 09:00, 12:00)
    check_time_1 = os.getenv("CHECK_TIME_1", "09:00").strip()
    check_time_2 = os.getenv("CHECK_TIME_2", "12:00").strip()

    # 시간 파싱 함수
    def parse_time(time_str):
        """HH:MM 형식의 시간 문자열을 파싱하여 (hour, minute) 튜플 반환"""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError(
                    "시간 형식이 올바르지 않습니다. HH:MM 형식을 사용하세요."
                )
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("시간 범위가 올바르지 않습니다. (00:00 ~ 23:59)")
            return hour, minute
        except (ValueError, IndexError) as e:
            print(f"시간 파싱 오류: {time_str} - {e}")
            return None, None

    # 첫 번째 스케줄 시간 파싱 및 등록
    hour1, minute1 = parse_time(check_time_1)
    if hour1 is not None and minute1 is not None:
        scheduler.add_job(
            check_unchecked_items,
            trigger=CronTrigger(hour=hour1, minute=minute1, timezone="Asia/Seoul"),
            id="check_time_1",
            name=f"체크리스트 확인 ({check_time_1})",
            replace_existing=True,
        )
        print(f"스케줄 등록: 매일 {check_time_1}에 체크리스트 확인")
    else:
        print(f"경고: CHECK_TIME_1 ({check_time_1}) 파싱 실패, 기본값 09:00 사용")
        scheduler.add_job(
            check_unchecked_items,
            trigger=CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
            id="check_time_1",
            name="체크리스트 확인 (09:00)",
            replace_existing=True,
        )

    # 두 번째 스케줄 시간 파싱 및 등록
    hour2, minute2 = parse_time(check_time_2)
    if hour2 is not None and minute2 is not None:
        scheduler.add_job(
            check_unchecked_items,
            trigger=CronTrigger(hour=hour2, minute=minute2, timezone="Asia/Seoul"),
            id="check_time_2",
            name=f"체크리스트 확인 ({check_time_2})",
            replace_existing=True,
        )
        print(f"스케줄 등록: 매일 {check_time_2}에 체크리스트 확인")
    else:
        print(f"경고: CHECK_TIME_2 ({check_time_2}) 파싱 실패, 기본값 12:00 사용")
        scheduler.add_job(
            check_unchecked_items,
            trigger=CronTrigger(hour=12, minute=0, timezone="Asia/Seoul"),
            id="check_time_2",
            name="체크리스트 확인 (12:00)",
            replace_existing=True,
        )

    scheduler.start()
    print(
        f"스케줄러가 시작되었습니다. 매일 {check_time_1}, {check_time_2}에 미체크 항목을 확인합니다."
    )