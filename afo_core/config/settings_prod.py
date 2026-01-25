# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Production Settings
Phase 2-5: 환경별 설정 분리 - Production 환경
"""

from AFO.settings import AFOSettings


class AFOSettingsProd(AFOSettings):
    """
    Production 환경 설정
    기본 설정을 상속받고 프로덕션 환경에 맞게 오버라이드
    """

    # Production 환경 기본값
    MOCK_MODE: bool = False  # 프로덕션에서는 Mock 모드 비활성화
    ASYNC_QUERY_ENABLED: bool = True

    # Production 환경 로깅
    LOG_LEVEL: str = "INFO"

    # Production 환경 데이터베이스 (환경 변수에서 로드)
    # POSTGRES_HOST, POSTGRES_PORT 등은 환경 변수에서 필수로 설정

    # Production 환경 Redis (환경 변수에서 로드)
    # REDIS_HOST, REDIS_PORT 등은 환경 변수에서 필수로 설정

    # Production 환경 서비스 URL (환경 변수에서 로드)
    # 모든 서비스 URL은 환경 변수에서 필수로 설정

    # Production 환경 API Keys (환경 변수에서 필수로 로드)
    # 모든 API 키는 환경 변수에서 필수로 설정

    class Config:
        env_file = ".env.prod"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
