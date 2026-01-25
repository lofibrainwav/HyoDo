from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Settings Module (眞善美孝永)

Stub module for AFO settings to unblock Gate.
Full implementation pending.
"""


logger = logging.getLogger(__name__)


@dataclass
class AFOSettings:
    """AFO Kingdom Settings."""

    # Core settings
    environment: str = field(default_factory=lambda: os.getenv("AFO_ENV", "production"))
    debug: bool = field(default_factory=lambda: os.getenv("AFO_DEBUG", "false").lower() == "true")
    version: str = "1.0.0"

    # API settings
    api_host: str = field(default_factory=lambda: os.getenv("AFO_API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: int(os.getenv("AFO_API_PORT", "8010")))

    # LLM settings
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    default_model: str = field(
        default_factory=lambda: os.getenv("DSPY_OPENAI_MODEL", "gpt-4o-mini")
    )

    # Redis settings (Phase 35-1: Cache infrastructure)
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    REDIS_PASSWORD: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    REDIS_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("REDIS_TIMEOUT", "5")))
    REDIS_MAX_CONNECTIONS: int = field(
        default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    )

    def get_redis_url(self) -> str:
        """Get Redis URL for connection."""
        return self.redis_url

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "version": self.version,
            "api_host": self.api_host,
            "api_port": self.api_port,
        }


# Global settings instance
_settings: AFOSettings | None = None


def get_settings() -> AFOSettings:
    """Get AFO settings singleton."""
    global _settings
    if _settings is None:
        _settings = AFOSettings()
    return _settings


__all__ = ["AFOSettings", "get_settings"]
