#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys

from pydantic import ValidationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("config_checker")


def check_config() -> None:
    """왕국 설정 자가 진단 (眞)"""
    logger.info("🛡️  Starting Kingdom Configuration Audit...")

    try:
        from AFO.config.settings import get_settings

        settings = get_settings()

        # 1. Basic properties
        logger.info(f"✅ Settings Loaded: {settings.__class__.__name__}")
        logger.info(f"📍 Database (PG): {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        logger.info(f"📍 Redis: {settings.get_redis_url()}")
        logger.info(f"📍 Ollama: {settings.OLLAMA_BASE_URL} (Model: {settings.OLLAMA_MODEL})")

        # 2. Validation check (numeric ranges)
        logger.info(f"✅ Redis Max Connections: {settings.REDIS_MAX_CONNECTIONS}")
        logger.info(f"✅ Ollama Timeout: {settings.OLLAMA_TIMEOUT}s")

        logger.info("✨ Configuration Audit PASSED! (眞)")
        return True

    except ValidationError as e:
        logger.error(f"❌ Configuration Validation FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected Error during audit: {e}")
        return False


if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
