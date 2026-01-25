# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Test Settings
Phase 2-5: 환경별 설정 분리 - Test 환경
"""

from AFO.settings import AFOSettings


class AFOSettingsTest(AFOSettings):
    """
    Test 환경 설정
    기본 설정을 상속받고 테스트 환경에 맞게 오버라이드
    """

    # Test 환경 기본값
    MOCK_MODE: bool = True  # 테스트 시 Mock 모드 활성화
    ASYNC_QUERY_ENABLED: bool = False  # 테스트에서는 동기 실행 선호

    # Test 환경 로깅
    LOG_LEVEL: str = "WARNING"  # 테스트에서는 최소 로깅

    # Test 환경 데이터베이스 (테스트용)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 15433  # 테스트용 포트 (프로덕션과 분리)
    POSTGRES_DB: str = "afo_memory_test"

    # Test 환경 Redis (테스트용)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380  # 테스트용 포트 (프로덕션과 분리)

    # Test 환경 서비스 URL (Mock 서버 또는 테스트용)
    OLLAMA_BASE_URL: str = "http://localhost:11435"  # 테스트용 포트
    VECTOR_DB: str = "lancedb"  # 테스트용 벡터 DB
    LANCEDB_PATH: str = "./data/test_lancedb"  # 테스트용 LanceDB 경로
    N8N_URL: str = "http://localhost:5679"  # 테스트용 포트
    API_WALLET_URL: str = "http://localhost:8001"  # 테스트용 포트
    MCP_SERVER_URL: str = "http://localhost:8788"  # 테스트용 포트

    # Test 환경 API Keys (Mock 키 사용)
    # 실제 API 키는 사용하지 않고 Mock 응답 사용

    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
