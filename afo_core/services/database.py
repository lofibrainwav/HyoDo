# Trinity Score: 90.0 (Established by Chancellor)
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException

if TYPE_CHECKING:
    import asyncpg

# 중앙 설정 사용
from AFO.config.settings import get_settings

# Lazy import asyncpg to avoid startup errors if not installed
try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    asyncpg = None
    ASYNCPG_AVAILABLE = False


# ============================================================================
# Connection Pool (성능 최적화)
# ============================================================================
_pool: Any | None = None


async def get_pool() -> Any:
    """
    비동기 PostgreSQL 커넥션 풀 반환 (싱글톤 패턴)

    Returns:
        asyncpg.Pool: PostgreSQL 커넥션 풀
    """
    global _pool

    if not ASYNCPG_AVAILABLE or asyncpg is None:
        raise HTTPException(status_code=503, detail="PostgreSQL async support not available")

    if _pool is not None:
        return _pool

    try:
        settings = get_settings()
        params = settings.get_postgres_connection_params()

        # 커넥션 풀 설정
        pool_config = {
            "min_size": 2,
            "max_size": settings.POSTGRES_POOL_SIZE,
            "max_inactive_connection_lifetime": settings.POSTGRES_POOL_RECYCLE,
        }

        # DATABASE_URL이 있으면 사용, 없으면 개별 파라미터 사용
        if "database_url" in params:
            _pool = await asyncpg.create_pool(params["database_url"], **pool_config)
        else:
            _pool = await asyncpg.create_pool(
                host=params["host"],
                port=params["port"],
                database=params["database"],
                user=params["user"],
                password=params["password"],
                **pool_config,
            )
        print(f"✅ PostgreSQL 커넥션 풀 생성 (size={settings.POSTGRES_POOL_SIZE})")
        return _pool
    except Exception as e:
        print(f"❌ PostgreSQL 풀 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 풀 생성 실패") from e


async def close_pool() -> None:
    """커넥션 풀 종료"""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        print("✅ PostgreSQL 커넥션 풀 종료")


# [論語]學而不思則罔 - 배우되 생각하지 않으면 어둡다
async def get_db_connection() -> Any:
    """
    비동기 PostgreSQL 연결 함수 (커넥션 풀 사용)

    Returns:
        asyncpg.Connection: PostgreSQL 연결 객체 (풀에서 획득)
    """
    pool = await get_pool()
    return await pool.acquire()
