# Gmail → 회사 도메인 포워딩 설정 가이드

## 개요

Gmail SMTP를 사용하여 메일을 발송하되, 발신자가 회사 도메인으로 보이도록 설정합니다.

## 설정 방법

### 1. Gmail 앱 비밀번호 생성

1. **Google 계정** 접속: https://myaccount.google.com/
2. **보안** → **2단계 인증** 활성화 (필수)
3. **앱 비밀번호** 생성:
   - 보안 → 앱 비밀번호
   - 앱 선택: "메일"
   - 기기 선택: "기타(맞춤 이름)" → "QA 체크리스트"
   - 생성된 16자리 비밀번호 복사

### 2. .env 파일 설정

`backend/.env` 파일에 다음 설정을 추가하세요:

```env
# Gmail SMTP 설정
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=앱_비밀번호_16자리
SMTP_FROM_EMAIL=회사_이메일@ajnet.co.kr
SMTP_FROM_NAME=QA 체크리스트 시스템
SMTP_USE_SSL=false
```

**설명:**
- `SMTP_USER`: Gmail 주소 (예: `your-email@gmail.com`)
- `SMTP_PASSWORD`: Gmail 앱 비밀번호 (16자리)
- `SMTP_FROM_EMAIL`: 회사 도메인 이메일 (예: `kimhs@ajnet.co.kr`)
- `SMTP_FROM_NAME`: 발신자 이름 (선택사항, 기본값: "QA 체크리스트 시스템")

### 3. Gmail에서 회사 도메인으로 포워딩 설정 (선택사항)

Gmail에서 회사 이메일로 자동 포워딩을 설정하면, 회신 메일을 받을 수 있습니다:

1. **Gmail 설정** → **전달 및 POP/IMAP**
2. **이메일 전달** → **새 전달 주소 추가**
3. 회사 이메일 주소 입력 (예: `kimhs@ajnet.co.kr`)
4. **전달된 메일 복사본을 받지 않음** 선택 (중복 방지)

## 작동 방식

1. **메일 발송**: Gmail SMTP 서버를 통해 메일 발송
2. **발신자 표시**: From 헤더에 회사 도메인 이메일 설정
3. **회신 주소**: Reply-To 헤더에 회사 도메인 이메일 설정
4. **수신자 관점**: 대부분의 메일 클라이언트에서 회사 도메인으로 표시됨

## 주의사항

### Gmail의 발신자 검증

Gmail은 발신자 주소를 검증하므로:
- **From 헤더**는 회사 도메인으로 설정되지만
- **실제 발신자**는 Gmail 계정입니다
- 일부 메일 클라이언트에서는 "via gmail.com" 또는 "on behalf of" 표시가 나타날 수 있습니다

### 스팸 필터링

- 일부 스팸 필터에서 Gmail을 통해 회사 도메인으로 보내는 메일을 의심할 수 있습니다
- SPF, DKIM 레코드가 회사 도메인에 설정되어 있지 않으면 스팸으로 분류될 수 있습니다

### 해결 방법

완전히 회사 도메인으로 보이게 하려면:
1. **회사 SMTP 서버 직접 사용** (권장)
2. **Gmail Workspace 사용** (회사 도메인을 Gmail Workspace에 연결)
3. **전용 메일 서버 구축**

## 테스트

설정 후 다음 명령어로 테스트하세요:

```bash
cd backend
python test_email.py
```

또는:

```bash
python test_gmail_forwarding.py
```

## 문제 해결

### "앱 비밀번호를 사용할 수 없습니다"
- 2단계 인증이 활성화되어 있는지 확인
- Google Workspace 계정은 관리자가 앱 비밀번호를 허용해야 함

### "인증 실패"
- 앱 비밀번호가 올바른지 확인 (일반 비밀번호가 아님)
- Gmail 계정이 활성화되어 있는지 확인

### "메일이 스팸으로 분류됨"
- 회사 도메인의 SPF 레코드에 Gmail SMTP 서버 추가 필요
- IT 부서에 문의하여 DNS 레코드 수정 요청

