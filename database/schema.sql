-- DX본부 시스템 체크리스트 데이터베이스 스키마

-- 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,  -- 사번
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 시스템 구분 테이블
CREATE TABLE systems (
    id SERIAL PRIMARY KEY,
    system_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 체크 항목 테이블
CREATE TABLE check_items (
    id SERIAL PRIMARY KEY,
    system_id INTEGER REFERENCES systems(id) ON DELETE CASCADE,
    item_name VARCHAR(200) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자-시스템 담당 관계 테이블
CREATE TABLE user_system_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    system_id INTEGER REFERENCES systems(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, system_id)
);

-- 체크리스트 기록 테이블
CREATE TABLE checklist_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    check_item_id INTEGER REFERENCES check_items(id) ON DELETE CASCADE,
    check_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('PASS', 'FAIL')),
    notes TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, check_item_id, check_date)
);

-- 특이사항 테이블
CREATE TABLE special_notes (
    id SERIAL PRIMARY KEY,
    check_item_id INTEGER REFERENCES check_items(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_checklist_records_date ON checklist_records(check_date);
CREATE INDEX idx_checklist_records_user_date ON checklist_records(user_id, check_date);
CREATE INDEX idx_user_system_assignments_user ON user_system_assignments(user_id);
CREATE INDEX idx_user_system_assignments_system ON user_system_assignments(system_id);

