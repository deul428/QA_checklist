-- 체크리스트 관련 테이블 인덱스 최적화 스크립트
-- 성능 향상을 위한 인덱스 추가

-- checklist_records 테이블 인덱스 최적화
-- 현재 상태 조회 최적화: check_item_id, check_date, environment 조합으로 자주 조회됨
CREATE INDEX IF NOT EXISTS idx_checklist_records_item_date_env 
ON checklist_records(check_item_id, check_date, environment);

-- 사용자별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_checklist_records_user_date_env 
ON checklist_records(user_id, check_date, environment);

-- 시스템별 조회 최적화 (성능 향상을 위한 비정규화 필드 활용)
CREATE INDEX IF NOT EXISTS idx_checklist_records_system_date_env 
ON checklist_records(system_id, check_date, environment);

-- checklist_records_logs 테이블 인덱스 최적화
-- 이력 조회 최적화: check_item_id, check_date, created_at 조합으로 시간순 조회
CREATE INDEX IF NOT EXISTS idx_checklist_records_logs_item_date_created 
ON checklist_records_logs(check_item_id, check_date, created_at);

-- 사용자별 로그 조회 최적화
CREATE INDEX IF NOT EXISTS idx_checklist_records_logs_user_date 
ON checklist_records_logs(user_id, check_date);

-- 액션별 필터링 최적화
CREATE INDEX IF NOT EXISTS idx_checklist_records_logs_action 
ON checklist_records_logs(action);

-- 환경별 필터링 최적화
CREATE INDEX IF NOT EXISTS idx_checklist_records_logs_env_date 
ON checklist_records_logs(environment, check_date);

-- 시스템별 로그 조회 최적화
CREATE INDEX IF NOT EXISTS idx_checklist_records_logs_system_date 
ON checklist_records_logs(system_id, check_date);

