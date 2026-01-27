-- admin_logs 테이블의 외래 키 제약 조건 추가 스크립트
-- admin_user_id를 users.user_id에 참조하도록 설정

-- 1. 외래 키 체크 비활성화
PRAGMA foreign_keys = OFF;

-- 2. 새 테이블 생성 (외래 키 포함)
CREATE TABLE admin_logs_new (
    id INTEGER PRIMARY KEY,
    admin_user_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('system', 'check_item', 'assignment')),
    entity_id INTEGER NULL,
    old_data TEXT NULL,
    new_data TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 3. 기존 데이터 복사
INSERT INTO admin_logs_new 
SELECT * FROM admin_logs;

-- 4. 기존 테이블 삭제
DROP TABLE admin_logs;

-- 5. 새 테이블 이름 변경
ALTER TABLE admin_logs_new RENAME TO admin_logs;

-- 6. 인덱스 재생성
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_user_id ON admin_logs(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_logs_entity_type ON admin_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_admin_logs_entity_id ON admin_logs(entity_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at);

-- 7. 외래 키 체크 다시 활성화
PRAGMA foreign_keys = ON;

