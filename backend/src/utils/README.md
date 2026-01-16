# 유틸리티 스크립트

이 디렉토리에는 데이터베이스 관리 및 유지보수를 위한 유틸리티 스크립트들이 포함되어 있습니다.

## 포함된 스크립트

### 데이터 임포트
- `import_checklist_data.py` - 체크리스트 데이터 CSV 임포트
- `import_user_copy_csv.py` - 사용자 데이터 CSV 임포트

### 데이터베이스 관리
- `create_views.py` - 데이터베이스 조회 편의를 위한 VIEW 생성
- `backup_and_update_user_emails.py` - 사용자 이메일 백업 및 테스트용 변경
- `restore_user_emails.py` - 백업된 사용자 이메일 복원

### 스케줄러 관리
- `cancel_scheduled_job.py` - 예약된 스케줄 작업 취소

## 사용법

각 스크립트는 독립적으로 실행할 수 있으며, 프로젝트 루트에서 실행해야 합니다.

```bash
# 체크리스트 데이터 임포트
python backend/src/utils/import_checklist_data.py [CSV 파일 경로]

# 사용자 데이터 임포트
python backend/src/utils/import_user_copy_csv.py

# VIEW 생성
python backend/src/utils/create_views.py

# 스케줄 작업 취소
python backend/src/utils/cancel_scheduled_job.py [job_id]
```

