# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom System Cleanup

Handles system component cleanup during FastAPI lifespan shutdown.
"""

import logging
from contextlib import suppress

logger = logging.getLogger(__name__)


async def cleanup_system() -> None:
    """Cleanup all AFO Kingdom system components."""
    print("[영덕] 영덕 완전체 종료 중...")

    try:
        # Cleanup Yeongdeok system
        await _cleanup_yeongdeok()

        # Cleanup database connections
        await _cleanup_databases()

        print("[지휘소 v6】 API 서버 가동 중지.")

    except Exception as e:
        logger.error(f"System cleanup failed: {e}")
        # Don't re-raise cleanup errors to avoid masking startup errors


async def _cleanup_yeongdeok() -> None:
    """Cleanup Yeongdeok Complete system."""
    try:
        # Import here to avoid circular imports during initialization
        from AFO.api.initialization import yeongdeok

        if yeongdeok and hasattr(yeongdeok, "browser"):
            await yeongdeok.close_eyes()
            print("✅ Yeongdeok browser cleanup completed")
    except Exception as e:
        logger.warning(f"Yeongdeok cleanup failed: {e}")


async def _cleanup_databases() -> None:
    """Cleanup database connections."""
    try:
        # Import here to avoid circular imports during initialization
        from AFO.api.initialization import PG_POOL, REDIS_CLIENT

        # Cleanup PostgreSQL connection pool
        if PG_POOL:
            with suppress(Exception):
                PG_POOL.closeall()
                print("✅ PostgreSQL connection pool closed")

        # Cleanup Redis connection
        if REDIS_CLIENT:
            with suppress(Exception):
                REDIS_CLIENT.close()
                print("✅ Redis connection closed")

    except Exception as e:
        logger.warning(f"Database cleanup failed: {e}")
