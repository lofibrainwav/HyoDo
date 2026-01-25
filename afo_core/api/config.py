from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

from AFO.api.cleanup import cleanup_system
from AFO.api.compat import get_settings_safe
from AFO.api.initialization import initialize_system
from AFO.api.metadata import get_api_metadata

# Load environment variables from .env file
load_dotenv()
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)  # Load package level .env

# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Kingdom API Configuration Module (아름다운 코드 적용)

Trinity Score 기반 아름다운 코드로 구현된 FastAPI 설정 및 라이프사이클 관리.
모듈화, 타입 안전성, 문서화를 통해 안정성과 확장성을 보장.

Author: AFO Kingdom Development Team
Date: 2025-12-24
Version: 2.0.0 (Beautiful Code Edition)
"""


# Configure logging
logger = logging.getLogger(__name__)


class APIConfig:
    """
    AFO Kingdom API Configuration (아름다운 코드 적용)

    Trinity Score 기반 API 설정을 체계적으로 관리.
    환경 변수와 설정 파일을 통합하여 안정적인 구성을 제공.

    Attributes:
        host: API 서버 호스트
        port: API 서버 포트
        debug: 디버그 모드 여부
        cors_origins: CORS 허용 오리진
    """

    def __init__(self) -> None:
        """Initialize API configuration with beautiful code principles."""
        self.settings = get_settings_safe()
        self._load_configuration()

        logger.info("API Configuration initialized with beautiful code principles")

    def _load_configuration(self) -> None:
        """Load configuration from settings and environment variables."""
        # Server configuration - Security improvement: avoid binding to all interfaces
        self.host = os.getenv("API_SERVER_HOST", "127.0.0.1")
        self.port = int(os.getenv("API_SERVER_PORT", "8000"))

        # Application configuration
        self.debug = self._get_config_value("AFO_DEBUG", "true").lower() == "true"
        self.cors_origins = self._get_cors_origins()

        logger.debug(
            f"Configuration loaded: host={self.host}, port={self.port}, debug={self.debug}"
        )

    def _get_config_value(self, key: str, default: str) -> str:
        """Get configuration value with fallback hierarchy."""
        # 1. Settings object
        if self.settings and hasattr(self.settings, key):
            value = getattr(self.settings, key)
            if value is not None:
                return str(value)

        # 2. Environment variable
        env_value = os.getenv(key)
        if env_value:
            return env_value

        # 3. Default value
        return default

    def _get_cors_origins(self) -> list[str]:
        """Get CORS origins configuration."""
        cors_env = os.getenv("AFO_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]


class AppFactory:
    """
    FastAPI Application Factory (아름다운 코드 적용)

    Trinity Score 기반 FastAPI 앱 생성을 체계적으로 관리.
    메타데이터, 라이프사이클, 미들웨어를 통합하여 안정적인 앱 생성 보장.

    Attributes:
        config: API 설정 객체
    """

    def __init__(self, config: APIConfig) -> None:
        """Initialize application factory.

        Args:
            config: API configuration object
        """
        self.config = config

    def create_application(self) -> FastAPI:
        """
        Create and configure FastAPI application instance.

        Trinity Score: 美 (Beauty) - 체계적이고 아름다운 앱 구성

        Returns:
            Configured FastAPI application
        """
        try:
            metadata = get_api_metadata()

            app = FastAPI(
                lifespan=self._get_lifespan_manager(),
                debug=self.config.debug,
                **metadata,
            )

            logger.info("FastAPI application created successfully")
            return app

        except Exception as e:
            logger.error(f"Failed to create FastAPI application: {e}")
            raise

    def _get_lifespan_manager(self) -> Any:
        """Get lifespan manager for FastAPI application."""
        return get_lifespan_manager


class LifespanManager:
    """
    Application Lifespan Manager (아름다운 코드 적용)

    Trinity Score 기반 애플리케이션 라이프사이클을 체계적으로 관리.
    초기화와 정리 작업을 안전하고 예측 가능하게 수행.

    Attributes:
        initialized: 초기화 완료 상태
        cleanup_performed: 정리 작업 수행 상태
    """

    def __init__(self) -> None:
        """Initialize lifespan manager."""
        self.initialized = False
        self.cleanup_performed = False

    @asynccontextmanager
    async def get_lifespan_manager(self, app: FastAPI | None = None) -> Any:
        """
        Manage application lifecycle with proper initialization and cleanup.

        Trinity Score: 孝 (Serenity) - 마찰 없는 라이프사이클 관리

        Args:
            app: FastAPI app instance (optional, for FastAPI compatibility)

        Yields:
            None - allows application to run
        """
        try:
            # Initialize system components
            await self._initialize_system()
            self.initialized = True
            logger.info("Application lifespan: initialization completed")

            yield

        except Exception as e:
            logger.error(f"Application lifespan error: {e}")
            raise
        finally:
            # Cleanup system components
            await self._cleanup_system()
            self.cleanup_performed = True
            logger.info("Application lifespan: cleanup completed")

    async def _initialize_system(self) -> None:
        """
        Initialize system components.

        Trinity Score: 眞 (Truth) - 정확한 초기화로 안정성 보장
        """
        try:
            # Import here to avoid circular imports

            await initialize_system()
            logger.debug("System initialization completed")

        except ImportError:
            logger.warning("Initialization module not available, skipping")
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise

    async def _cleanup_system(self) -> None:
        """
        Cleanup system components.

        Trinity Score: 善 (Goodness) - 안전한 정리로 리소스 관리
        """
        try:
            # Import here to avoid circular imports

            await cleanup_system()
            logger.debug("System cleanup completed")

        except ImportError:
            logger.warning("Cleanup module not available, skipping")
        except Exception as e:
            logger.error(f"System cleanup failed: {e}")
            # Don't re-raise cleanup errors to avoid masking startup errors


class ServerConfig:
    """
    Server Configuration Manager (아름다운 코드 적용)

    Trinity Score 기반 서버 설정을 체계적으로 관리.
    호스트, 포트, 환경 설정을 검증하고 제공.

    Attributes:
        config: API 설정 객체
    """

    def __init__(self, config: APIConfig) -> None:
        """Initialize server configuration.

        Args:
            config: API configuration object
        """
        self.config = config

    def get_server_config(self) -> tuple[str, int]:
        """
        Get validated server host and port configuration.

        Trinity Score: 眞 (Truth) - 검증된 설정으로 정확성 보장

        Returns:
            Tuple of (host, port)
        """
        try:
            # Validate host
            if not self.config.host or not isinstance(self.config.host, str):
                raise ValueError("Invalid host configuration")

            # Validate port
            if not isinstance(self.config.port, int) or self.config.port <= 0:
                raise ValueError("Invalid port configuration")

            logger.debug(f"Server config validated: {self.config.host}:{self.config.port}")
            return self.config.host, self.config.port

        except Exception as e:
            logger.error(f"Server configuration validation failed: {e}")
            # Return safe defaults
            return "127.0.0.1", 8010


# Global instances (Singleton pattern for beautiful code)
api_config = APIConfig()
lifespan_manager = LifespanManager()


# Public API functions with backward compatibility
def get_app_config() -> FastAPI:
    """Create and configure FastAPI application instance (backward compatibility)."""
    factory = AppFactory(api_config)
    return factory.create_application()


def get_server_config() -> tuple[str, int]:
    """Get server host and port configuration (backward compatibility)."""
    server_config = ServerConfig(api_config)
    return server_config.get_server_config()


@asynccontextmanager
async def get_lifespan_manager(app: FastAPI | None = None) -> Any:
    """Manage application lifecycle (backward compatibility)."""
    async with lifespan_manager.get_lifespan_manager(app):
        yield
