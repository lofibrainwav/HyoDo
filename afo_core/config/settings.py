# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO 왕국 중앙 집중식 설정 관리
Phase 1 리팩토링: 하드코딩 제거 및 환경 변수 통합
"""

import os
import sys
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from AFO.antigravity import antigravity
from AFO.julie import JulieConfig, julie_config
from AFO.trinity import TrinityConfig


class AFOSettings(BaseSettings):
    """
    AFO 왕국 중앙 설정 클래스
    모든 환경 변수와 기본값을 한 곳에서 관리
    """

    # ============================================================================
    # AntiGravity Integration (Phase 1)
    # ============================================================================
    antigravity_mode: bool = Field(
        default=antigravity.AUTO_DEPLOY,
        description="AntiGravity 자동 배포 모드 (True: 활성화)",
    )

    # ============================================================================
    # Sub-Configurations (Phase 6A Centralization)
    # ============================================================================
    # Trinity SSOT (Class-based constant, not Pydantic)
    TRINITY: ClassVar[type[TrinityConfig]] = TrinityConfig

    # Julie CPA Config (Nested Pydantic)
    julie: JulieConfig = Field(default_factory=lambda: julie_config)

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ============================================================================
    # Database Settings (PostgreSQL)
    # NOTE: Defaults are set for Docker environment. Override via env vars for local dev.
    # ============================================================================
    POSTGRES_HOST: str = Field(default="afo-postgres", description="PostgreSQL 호스트")
    POSTGRES_PORT: int = Field(
        default=5432, description="PostgreSQL 포트 (Docker 내부 5432, 로컬 15432)"
    )
    POSTGRES_DB: str = Field(default="afo_memory", description="PostgreSQL 데이터베이스 이름")
    POSTGRES_USER: str = Field(default="afo", description="PostgreSQL 사용자")
    # Phase 15 Security Seal: 하드코딩된 시크릿 제거
    # 프로덕션에서는 반드시 환경변수로 설정 필요
    POSTGRES_PASSWORD: str = Field(
        default="",
        description="PostgreSQL 비밀번호 (환경변수 POSTGRES_PASSWORD로 설정 필수)",
    )
    DATABASE_URL: str | None = Field(
        default=None, description="PostgreSQL 연결 URL (선택적, 개별 설정보다 우선)"
    )

    # Connection Pool Settings (성능 최적화)
    POSTGRES_POOL_SIZE: int = Field(
        default=10, ge=1, le=100, description="PostgreSQL 커넥션 풀 크기"
    )
    POSTGRES_POOL_RECYCLE: int = Field(
        default=3600, ge=0, description="커넥션 재활용 주기 (초, DB 타임아웃 방지)"
    )

    # ============================================================================
    # Redis Settings
    # NOTE: Defaults are set for Docker environment. Override via env vars for local dev.
    # ============================================================================
    REDIS_URL: str = Field(default="redis://afo-redis:6379", description="Redis 연결 URL")
    REDIS_HOST: str = Field(
        default="afo-redis",
        description="Redis 호스트 (Docker: afo-redis, 로컬: localhost)",
    )
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535, description="Redis 포트")
    REDIS_TIMEOUT: int = Field(default=5, ge=1, le=300, description="Redis 연결 타임아웃 (초)")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, ge=1, le=1000, description="Redis 최대 연결 수")
    CACHE_DEFAULT_TTL: int = Field(default=3600, ge=0, description="기본 캐시 만료 시간 (초)")

    # ============================================================================
    # Vector Store Settings (LanceDB)
    # ============================================================================
    VECTOR_DB: str = Field(default="lancedb", description="벡터 DB 타입 (lancedb, qdrant, chroma)")
    LANCEDB_PATH: str = Field(default="./data/lancedb", description="LanceDB 데이터베이스 경로")
    EMBED_DIM: str = Field(
        default="dynamic", description="임베딩 차원 (dynamic=자동 감지, 숫자=고정값)"
    )
    VISION_MODEL: str = Field(default="qwen3-vl:latest", description="비전 모델")
    EMBED_MODEL: str = Field(
        default="embeddinggemma", description="임베딩 모델 (embeddinggemma 등)"
    )
    LANCEDB_DEFAULT_DIM: int = Field(
        default=768, description="기본 벡터 차원 (Ollama: 768, OpenAI: 1536)"
    )
    RAG_MAX_DOCUMENTS: int = Field(default=5, description="RAG 검색 시 최대 문서 수")
    BUILD_VECTOR_INDEX: str = Field(
        default="0", description="벡터 인덱스 생성 여부 (0=생성안함, 1=생성)"
    )

    # ============================================================================
    # Ollama Settings
    # NOTE: Defaults use host.docker.internal for Mac Docker. Override via env vars as needed.
    # ============================================================================
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434", description="Ollama LLM 서버 URL"
    )
    OLLAMA_MODEL: str = Field(default="qwen2.5-coder:7b", description="Ollama 기본 모델")
    OLLAMA_TIMEOUT: int = Field(default=120, ge=1, le=3600, description="Ollama API 타임아웃 (초)")
    OLLAMA_MAX_RETRIES: int = Field(default=3, ge=0, le=10, description="Ollama API 재시도 횟수")

    # ============================================================================
    # N8N Settings
    # ============================================================================
    N8N_URL: str = Field(
        default="http://localhost:5678", description="N8N 워크플로우 자동화 서버 URL"
    )

    # ============================================================================
    # API Wallet Settings
    # ============================================================================
    API_WALLET_URL: str = Field(default="http://localhost:8000", description="API Wallet 서버 URL")

    # ============================================================================
    # MCP Server Settings
    # ============================================================================
    MCP_SERVER_URL: str = Field(
        default="http://localhost:8787",
        description="MCP (Model Context Protocol) 서버 URL",
    )

    # ============================================================================
    # API Keys
    # Phase 15 Security Seal: 하드코딩된 시크릿 제거
    # ============================================================================
    API_YUNGDEOK: str = Field(default="", description="영덕 API 키 (환경변수 API_YUNGDEOK로 설정)")
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API 키")
    ANTHROPIC_API_KEY: str | None = Field(default=None, description="Anthropic (Claude) API 키")
    GEMINI_API_KEY: str | None = Field(default=None, description="Google Gemini API 키")
    GOOGLE_API_KEY: str | None = Field(
        default=None, description="Google API 키 (GEMINI_API_KEY 대체용)"
    )
    CHATGPT_SESSION_TOKEN_1: str | None = Field(default=None, description="ChatGPT 세션 토큰 1")
    CHATGPT_SESSION_TOKEN_2: str | None = Field(default=None, description="ChatGPT 세션 토큰 2")
    CHATGPT_SESSION_TOKEN_3: str | None = Field(default=None, description="ChatGPT 세션 토큰 3")
    CURSOR_ACCESS_TOKEN: str | None = Field(default=None, description="Cursor 액세스 토큰")
    REDIS_PASSWORD: str | None = Field(default=None, description="Redis 비밀번호")

    # ============================================================================
    # Application Settings
    # ============================================================================
    AFO_API_VERSION: str = Field(default="v1", description="AFO API 버전")
    INPUT_SERVER_PORT: int = Field(default=4200, description="Input Server 포트")
    INPUT_SERVER_HOST: str = Field(default="127.0.0.1", description="Input Server 호스트")
    DASHBOARD_URL: str = Field(
        default="http://localhost:3000",
        description="프론트엔드 대시보드 URL (GenUI 등)",
    )
    MAX_MEMORY_MB: int = Field(default=512, description="애플리케이션 최대 메모리 사용 제한 (MB)")

    # ============================================================================
    # API Server Settings
    # ============================================================================
    API_SERVER_PORT: int = Field(default=8010, description="API Server 포트 (Soul Engine)")
    API_SERVER_HOST: str = Field(default="127.0.0.1", description="API Server 호스트")
    SOUL_ENGINE_PORT: int = Field(default=8010, description="Soul Engine 포트 (5 Pillars 등)")
    ASYNC_QUERY_ENABLED: bool = Field(default=True, description="비동기 쿼리 활성화 여부")
    MOCK_MODE: bool = Field(default=False, description="Mock 모드 활성화 여부")
    IRS_MOCK_MODE: bool = Field(default=True, description="IRS Monitor Mock 모드 활성화 여부")
    IRS_RSS_URL: str = Field(
        default="https://www.irs.gov/newsroom/rss", description="IRS RSS Feed URL"
    )
    SENTRY_DSN: str | None = Field(default=None, description="Sentry DSN (에러 모니터링)")
    VAULT_ENABLED: bool = Field(default=False, description="Vault KMS 사용 여부")
    API_WALLET_ENCRYPTION_KEY: str | None = Field(
        default=None, description="API Wallet 암호화 키 (Fernet, 44자)"
    )
    # Vault Settings (Phase 3)
    VAULT_URL: str = Field(default="http://localhost:8200", description="Vault 서버 URL")
    VAULT_TOKEN: str | None = Field(default=None, description="Vault 액세스 토큰")
    TAVILY_API_KEY: str | None = Field(default=None, description="Tavily API 키 (웹 검색)")
    REDIS_RAG_INDEX: str = Field(default="rag_docs", description="Redis RAG 인덱스 이름")
    AFO_HOME: str | None = Field(default=None, description="AFO 홈 디렉토리 경로")
    AFO_SOUL_ENGINE_HOME: str | None = Field(
        default=None, description="AFO Soul Engine 홈 디렉토리 경로"
    )
    BASE_DIR: str = Field(
        default=os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        ),
        description="프로젝트 루트 디렉토리",
    )
    ARTIFACTS_DIR: str = Field(
        default=os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            ),
            "artifacts",
        ),
        description="아티팩트 및 증거 저장 디렉토리",
    )

    # ============================================================================
    # Chancellor Configuration (Optimization)
    # ============================================================================
    CHANCELLOR_AUTO_RUN_THRESHOLD: float = Field(
        default=90.0, description="자동 실행(AUTO_RUN)을 위한 최소 Trinity Score"
    )
    CHANCELLOR_RISK_THRESHOLD: float = Field(
        default=10.0, description="자동 실행(AUTO_RUN)을 위한 최대 Risk Score"
    )
    CHANCELLOR_MAX_MEMORY_ITEMS: int = Field(
        default=10, description="Chancellor 메모리 요약 트리거 임계값"
    )

    # ============================================================================
    # LLM Router Settings (Optimization)
    # ============================================================================
    AFO_LLM_MOCK_MODE: bool = Field(
        default=False, description="LLM 호출 Bypass 모드 (개발/테스트용)"
    )
    AFO_PILLAR_TIMEOUT: float = Field(default=15.0, description="Pillar 노드 LLM 타임아웃 (초)")

    # ============================================================================
    # Evolution System Configuration (Phase 36)
    # ============================================================================
    AUTO_MONITOR_INTERVAL: int = Field(default=3600, description="자율 모니터링 주기 (초)")

    # ============================================================================
    # Phase 23: Operation Hardening & Canary
    # ============================================================================
    CHANCELLOR_V2_ENABLED: bool = Field(
        default=False, description="Chancellor Graph V2 활성화 (Canary)"
    )
    CHANCELLOR_V2_SHADOW_ENABLED: bool = Field(
        default=False, description="Chancellor Graph V2 Shadow 모드 활성화"
    )
    CHANCELLOR_V2_DIFF_SAMPLING_RATE: float = Field(
        default=0.1, description="Shadow 모드 Diff 샘플링 비율 (0.0~1.0)"
    )
    OLLAMA_SWITCHING_PROTOCOL_ENABLED: bool = Field(
        default=True, description="Ollama 3단계 스위칭 프로토콜 활성화"
    )
    VAULT_STRICT_AUDIT: bool = Field(default=True, description="Vault 접근 감사 로그 활성화")
    VAULT_SEAL_KEY: str = Field(
        default="", description="Vault 봉인 키 (32 bytes base64, 비어있으면 자동 생성)"
    )
    VAULT_ENCRYPTION_METHOD: str = Field(
        default="fernet", description="암호화 방식 (fernet, aes-gcm)"
    )
    VAULT_AUDIT_FILE: str = Field(
        default="artifacts/vault/audit.jsonl", description="Vault 감사 로그 파일 경로"
    )
    VAULT_SEALED_SECRETS_FILE: str = Field(
        default="artifacts/vault/sealed_secrets.enc", description="봉인된 시크릿 파일 경로"
    )

    # ============================================================================
    # Chancellor V2 Routing Settings (Phase 23-24)
    # ============================================================================
    CHANCELLOR_V2_ENABLED: bool = Field(default=True, description="Chancellor V2 엔진 활성화")
    CHANCELLOR_V2_HEADER_ROUTING: bool = Field(
        default=True, description="X-AFO-Engine 헤더 기반 라우팅 활성화"
    )
    CHANCELLOR_V2_CANARY_PERCENT: int = Field(
        default=0, ge=0, le=100, description="V2로 라우팅할 트래픽 비율 (0-100%)"
    )
    CHANCELLOR_V2_SHADOW_MODE: bool = Field(
        default=False, description="Shadow 모드 (V2 백그라운드 실행, V1 응답)"
    )
    CHANCELLOR_V2_FALLBACK_TO_V1: bool = Field(default=True, description="V2 실패 시 V1으로 폴백")

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def get_postgres_connection_params(self) -> dict:
        """PostgreSQL 연결 파라미터 반환"""
        if self.DATABASE_URL:
            return {"database_url": self.DATABASE_URL}

        return {
            "host": self.POSTGRES_HOST,
            "port": self.POSTGRES_PORT,
            "database": self.POSTGRES_DB,
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD,
        }

    def get_redis_url(self) -> str:
        """Redis URL 반환"""
        if self.REDIS_URL and not self.REDIS_URL.startswith("redis://localhost"):
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


# 전역 설정 인스턴스 (싱글톤 패턴)
_settings: AFOSettings | None = None


def get_settings(env: str | None = None) -> AFOSettings:
    """
    전역 설정 인스턴스 반환 (싱글톤)

    Args:
        env: 환경 이름 ("dev", "prod", "test"). None이면 AFO_ENV 환경 변수 사용

    Returns:
        AFOSettings 인스턴스 (환경에 따라 AFOSettingsDev, AFOSettingsProd, AFOSettingsTest)
    """
    global _settings

    # 환경 변수에서 환경 확인 (Phase 2-5)
    if env is None:
        env = os.getenv("AFO_ENV", "dev").lower()

    # 환경별 설정 클래스 로드
    settings_class: type[AFOSettings]

    if env == "prod" or env == "production":
        try:
            from AFO.settings_prod import AFOSettingsProd

            settings_class = AFOSettingsProd
        except ImportError:
            # Fallback: 기본 설정 사용
            settings_class = AFOSettings
    elif env == "test" or env == "testing":
        try:
            from AFO.settings_test import AFOSettingsTest

            settings_class = AFOSettingsTest
        except ImportError:
            # Fallback: 기본 설정 사용
            settings_class = AFOSettings
    else:  # dev 또는 기본값
        try:
            from AFO.settings_dev import AFOSettingsDev

            settings_class = AFOSettingsDev
        except ImportError:
            # Fallback: 기본 설정 사용
            settings_class = AFOSettings

    # 싱글톤 인스턴스 생성
    if _settings is None:
        _settings = settings_class()

        # Context7 trinity-os 패키지 경로 추가 (Python Path 확장)
        # 환경변수 우선 사용, 없으면 자동 계산
        trinity_os_path = os.environ.get("AFO_TRINITY_OS_PATH")
        if not trinity_os_path:
            trinity_os_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "trinity-os")
            )

        if trinity_os_path and os.path.exists(trinity_os_path) and trinity_os_path not in sys.path:
            sys.path.insert(0, trinity_os_path)
            print(f"✅ Context7 trinity-os 경로 추가: {trinity_os_path}", file=sys.stderr)
        elif not os.path.exists(trinity_os_path):
            print(f"ℹ️ Context7 trinity-os 경로 없음: {trinity_os_path}", file=sys.stderr)
        else:
            print(
                f"✅ Context7 trinity-os 경로 이미 추가됨: {trinity_os_path}",
                file=sys.stderr,
            )

        print(
            f"✅ AFO 설정 로드 완료: {env} 환경 ({settings_class.__name__})",
            file=sys.stderr,
        )

    return _settings


# 편의를 위한 전역 인스턴스
settings = get_settings()
