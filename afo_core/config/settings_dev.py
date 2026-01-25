# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Development Settings
Phase 2-5: 환경별 설정 분리 - Development 환경
"""

from AFO.settings import AFOSettings


class AFOSettingsDev(AFOSettings):
    """
    Development 환경 설정
    기본 설정을 상속받고 개발 환경에 맞게 오버라이드

    NOTE: 환경변수가 우선합니다. Docker에서는 docker-compose.yml의
    environment 섹션에서 설정된 값(afo-redis, afo-postgres 등)이 사용됩니다.
    로컬 개발 시에는 .env 또는 환경변수를 통해 설정하세요.
    """

    # Development 환경 기본값
    MOCK_MODE: bool = False  # CLI 정기구독 사용 - Mock 불필요
    ASYNC_QUERY_ENABLED: bool = True

    # Development 환경 로깅
    LOG_LEVEL: str = "DEBUG"

    # NOTE: Database/Service hosts are NOT hardcoded here.
    # - Docker: Uses afo-redis, afo-postgres, afo-ollama from docker-compose.yml
    # - Local: Set via .env or environment variables
    # The base class (AFOSettings) provides defaults that can be overridden by env vars.

    # Development 환경 API Keys (선택적, .env에서 로드)
    # 실제 키는 .env 파일에서 관리

    class Config:
        env_file = ".env.dev"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
