-- 대체 담당자 할당 로그 테이블 생성 스크립트
-- substitute_assignments 테이블의 모든 변경 이력(추가, 수정, 삭제)을 기록합니다.

CREATE TABLE IF NOT EXISTS substitute_assignments_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    substitute_assignment_id INTEGER,  -- 대체 담당자 할당 ID (삭제된 경우를 위해 nullable)
    action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),  -- 작업 유형
    changed_by_user_id VARCHAR(50),  -- 변경한 사용자 ID
    old_data TEXT,  -- 변경 전 데이터 (JSON 문자열)
    new_data TEXT,  -- 변경 후 데이터 (JSON 문자열)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 변경 일시
    
    -- 외래 키 제약 조건
    FOREIGN KEY (substitute_assignment_id) REFERENCES substitute_assignments(id) ON DELETE SET NULL,
    FOREIGN KEY (changed_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_substitute_assignments_logs_assignment_id ON substitute_assignments_logs(substitute_assignment_id);
CREATE INDEX IF NOT EXISTS idx_substitute_assignments_logs_action ON substitute_assignments_logs(action);
CREATE INDEX IF NOT EXISTS idx_substitute_assignments_logs_changed_by ON substitute_assignments_logs(changed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_substitute_assignments_logs_created_at ON substitute_assignments_logs(created_at);

