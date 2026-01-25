# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO 설정 테스트
"""

from AFO.config.settings import get_settings


def test_get_settings() -> None:
    """설정 로드 테스트"""
    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "POSTGRES_HOST")
    assert hasattr(settings, "REDIS_URL")
    assert hasattr(settings, "VECTOR_DB")
    assert hasattr(settings, "LANCEDB_PATH")


def test_settings_defaults() -> None:
    """설정 기본값 테스트"""
    settings = get_settings()
    # Default is "afo-postgres" for docker-compose, can be overridden via env
    assert settings.POSTGRES_HOST in ("afo-postgres", "localhost")
    # Port is 5432 (standard) or 15432 (docker-compose external mapping)
    assert settings.POSTGRES_PORT in (5432, 15432)
    assert settings.REDIS_URL.startswith("redis://")


def test_get_postgres_connection_params() -> None:
    """PostgreSQL 연결 파라미터 테스트"""
    settings = get_settings()
    params = settings.get_postgres_connection_params()
    assert "host" in params or "database_url" in params
    assert "port" in params or "database_url" in params


def test_get_redis_url() -> None:
    """Redis URL 테스트"""
    settings = get_settings()
    redis_url = settings.get_redis_url()
    assert redis_url.startswith("redis://")
