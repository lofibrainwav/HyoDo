# Trinity Score: 90.0 (Established by Chancellor)
"""
Database Migrations for AFO Kingdom
사용자 시스템 및 관련 테이블 스키마 정의
"""

from typing import Any

# 사용자 시스템 스키마 (Phase 5)
USER_SYSTEM_SCHEMA = """
-- 사용자 테이블 (Phase 5: 인증/사용자 시스템)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 프로필 테이블 (확장성)
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- 사용자 세션 테이블 (Wallet 연동)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) DEFAULT 'local',
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API 키 사용량 추적 (Wallet 연동)
CREATE TABLE IF NOT EXISTS api_key_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    api_provider VARCHAR(50) NOT NULL,
    api_key_hash VARCHAR(128), -- 해시된 키로 추적 (보안)
    request_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    cost_accumulated DECIMAL(10,4) DEFAULT 0.0,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, api_provider, api_key_hash)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_user_provider ON api_key_usage(user_id, api_provider);

-- 트리거: updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 적용
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 사용자 생성 함수
CREATE OR REPLACE FUNCTION create_user(
    p_username VARCHAR(50),
    p_email VARCHAR(255),
    p_hashed_password VARCHAR(255),
    p_role VARCHAR(20) DEFAULT 'user'
) RETURNS INTEGER AS $$
DECLARE
    new_user_id INTEGER;
BEGIN
    INSERT INTO users (username, email, hashed_password, role)
    VALUES (p_username, p_email, p_hashed_password, p_role)
    RETURNING id INTO new_user_id;

    -- 기본 프로필 생성
    INSERT INTO user_profiles (user_id, display_name)
    VALUES (new_user_id, p_username);

    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql;

-- 사용자 조회 함수
CREATE OR REPLACE FUNCTION get_user_by_username(p_username VARCHAR(50))
RETURNS TABLE(
    id INTEGER,
    username VARCHAR(50),
    email VARCHAR(255),
    is_active BOOLEAN,
    is_verified BOOLEAN,
    role VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id, u.username, u.email, u.is_active, u.is_verified, u.role, u.created_at,
        p.display_name, p.avatar_url
    FROM users u
    LEFT JOIN user_profiles p ON u.id = p.user_id
    WHERE u.username = p_username AND u.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- 세션 생성 함수
CREATE OR REPLACE FUNCTION create_user_session(
    p_user_id INTEGER,
    p_session_token VARCHAR(255),
    p_provider VARCHAR(50) DEFAULT 'local',
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_expires_hours INTEGER DEFAULT 24
) RETURNS INTEGER AS $$
DECLARE
    new_session_id INTEGER;
BEGIN
    INSERT INTO user_sessions (
        user_id, session_token, provider, ip_address, user_agent, expires_at
    ) VALUES (
        p_user_id, p_session_token, p_provider, p_ip_address, p_user_agent,
        CURRENT_TIMESTAMP + INTERVAL '1 hour' * p_expires_hours
    )
    RETURNING id INTO new_session_id;

    -- 사용자 마지막 로그인 업데이트
    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = p_user_id;

    RETURN new_session_id;
END;
$$ LANGUAGE plpgsql;

-- 세션 검증 함수
CREATE OR REPLACE FUNCTION validate_user_session(p_session_token VARCHAR(255))
RETURNS TABLE(
    user_id INTEGER,
    username VARCHAR(50),
    role VARCHAR(20),
    expires_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.username, u.role, s.expires_at
    FROM user_sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.session_token = p_session_token
      AND s.expires_at > CURRENT_TIMESTAMP
      AND u.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;
"""


# 마이그레이션 실행 함수
async def run_user_system_migration() -> dict[str, Any]:
    """
    사용자 시스템 DB 마이그레이션 실행

    Returns:
        마이그레이션 결과
    """
    from AFO.services.database import get_db_connection

    try:
        conn = await get_db_connection()

        # 스키마 실행
        await conn.execute(USER_SYSTEM_SCHEMA)

        # 마이그레이션 기록 (간단한 버전 관리)
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
        """
        )

        # 현재 마이그레이션 기록
        await conn.execute(
            """
            INSERT INTO schema_migrations (version, description)
            VALUES ('user_system_v1', '사용자 시스템 기본 스키마 및 함수')
            ON CONFLICT (version) DO NOTHING;
        """
        )

        await conn.close()

        return {
            "status": "success",
            "message": "사용자 시스템 마이그레이션 완료",
            "tables_created": [
                "users",
                "user_profiles",
                "user_sessions",
                "api_key_usage",
                "schema_migrations",
            ],
            "functions_created": [
                "create_user",
                "get_user_by_username",
                "create_user_session",
                "validate_user_session",
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"마이그레이션 실패: {e}",
            "error": str(e),
        }
