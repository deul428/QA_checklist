# DX본부 시스템 체크리스트

시스템 체크리스트 관리 및 자동 알림 시스템

## 기술 스택

- **프론트엔드**: React + TypeScript
- **백엔드**: Python (FastAPI)
- **데이터베이스**: SQLite (개발) / PostgreSQL (운영)
- **배포**: AWS (예정)

## 프로젝트 구조

```
QA_checklist/
├── frontend/          # React + TypeScript 프론트엔드
├── backend/           # Python FastAPI 백엔드
├── database/          # DB 스키마 및 마이그레이션
└── README.md
```

## 주요 기능

1. **사번 기반 로그인**: 사용자 사번으로 로그인
2. **체크리스트 관리**: 담당 시스템의 체크리스트 항목 표시 및 PASS/FAIL 체크
3. **자동 알림**: 매일 09시/12시 미체크 항목에 대한 자동 메일 발송

## 설치 및 실행

### 백엔드 초기 설정

```bash 
cd E:\dev\projects\venv
python -m venv qa_checklist
E:\dev\projects\venv\qa_checklist\Scripts\activate
cd E:\dev\projects\QA_checklist\backend\src
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8003
```

### 프론트엔드 설정

```bash
cd E:\dev\projects\QA_checklist\frontend
npm install
npm start
```

### 데이터베이스 설정

#### SQLite 사용 (기본값, 권장)

별도 설치 없이 바로 사용 가능합니다. `.env` 파일이 없으면 자동으로 SQLite를 사용합니다.

```bash
cd backend
# .env 파일이 없으면 env.example을 복사
copy env.example .env
```

#### PostgreSQL 사용 (선택사항)

PostgreSQL을 사용하려면:

1. PostgreSQL 설치 및 실행
2. 데이터베이스 생성:
   ```sql
   CREATE DATABASE qa_checklist;
   ```
3. `.env` 파일에서 `DATABASE_URL`을 PostgreSQL로 변경:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/qa_checklist
   ```

## 환경 변수

백엔드 `.env` 파일 (`backend/env.example` 참고):

```bash
# SQLite 사용 (기본값)
DATABASE_URL=sqlite:///./qa_checklist.db

# 또는 PostgreSQL 사용
# DATABASE_URL=postgresql://user:password@localhost:5432/qa_checklist

SECRET_KEY=your-secret-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
```

**참고**: `.env` 파일이 없으면 자동으로 SQLite를 사용합니다.
