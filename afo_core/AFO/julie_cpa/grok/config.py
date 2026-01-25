"""Grok Configuration.

Grok 엔진 설정 및 환경 변수 관리.
"""

from __future__ import annotations

import os
from pathlib import Path


class GrokConfig:
    """Grok Engine Configuration."""

    XAI_API_KEY: str | None = os.getenv("XAI_API_KEY")
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    GROK_MODEL_BETA: str = "grok-beta"

    SESSION_FILE: str = ".grok_session.json"
    SESSION_PATH: Path = Path(__file__).parent.parent.parent.parent / SESSION_FILE

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    CACHE_TTL: int = 3600
    TRINITY_THRESHOLD: int = 90
