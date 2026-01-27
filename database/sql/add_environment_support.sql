-- 환경별 체크리스트 지원을 위한 스키마 변경
-- SQLite는 ALTER TABLE로 제약 조건을 직접 수정할 수 없으므로, 
-- 컬럼 추가 후 마이그레이션 스크립트에서 제약 조건을 처리합니다.

-- 1. systems 테이블에 환경 존재 여부 컬럼 추가
ALTER TABLE systems ADD COLUMN has_dev BOOLEAN DEFAULT 0 NOT NULL;
ALTER TABLE systems ADD COLUMN has_stg BOOLEAN DEFAULT 0 NOT NULL;
ALTER TABLE systems ADD COLUMN has_prd BOOLEAN DEFAULT 0 NOT NULL;

-- 2. check_items 테이블에 environment 컬럼 추가
ALTER TABLE check_items ADD COLUMN environment VARCHAR(10) DEFAULT 'prd' NOT NULL;

-- 3. checklist_records 테이블에 environment 컬럼 추가
ALTER TABLE checklist_records ADD COLUMN environment VARCHAR(10) DEFAULT 'prd' NOT NULL;

-- 4. checklist_records_logs 테이블에 environment 컬럼 추가
ALTER TABLE checklist_records_logs ADD COLUMN environment VARCHAR(10) DEFAULT 'prd' NOT NULL;

-- 5. user_system_assignments 테이블에 environment 컬럼 추가
ALTER TABLE user_system_assignments ADD COLUMN environment VARCHAR(10) DEFAULT 'prd' NOT NULL;

-- 인덱스 추가 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_check_items_system_env ON check_items(system_id, environment);
CREATE INDEX IF NOT EXISTS idx_checklist_records_item_date_env ON checklist_records(item_id, check_date, environment);
CREATE INDEX IF NOT EXISTS idx_checklist_records_env ON checklist_records(environment);
CREATE INDEX IF NOT EXISTS idx_user_system_assignments_env ON user_system_assignments(environment);

