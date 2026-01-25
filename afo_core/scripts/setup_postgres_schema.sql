-- AFO Kingdom PostgreSQL Schema Setup
-- Phase 1: Users 테이블 및 기본 스키마 생성

-- Users 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Family Hub 관련 테이블 (Phase 2 준비)
CREATE TABLE IF NOT EXISTS family_members (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_family_members_user_id ON family_members(user_id);

-- Family Hub 데이터 테이블 (Phase 2 준비)
CREATE TABLE IF NOT EXISTS family_hub_data (
    id SERIAL PRIMARY KEY,
    family_member_id INTEGER REFERENCES family_members(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_value JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_family_hub_data_member_id ON family_hub_data(family_member_id);
CREATE INDEX IF NOT EXISTS idx_family_hub_data_metric_type ON family_hub_data(metric_type);

-- 성공 메시지
SELECT 'AFO Kingdom PostgreSQL Schema Setup Complete!' AS status;

