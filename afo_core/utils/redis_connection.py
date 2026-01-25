# Trinity Score: 90.0 (Established by Chancellor)
"""
Redis 연결 통합 모듈
Phase 1 리팩토링: 중복 Redis 연결 로직 통합
"""

# 중앙 설정 사용
from typing import cast

import redis
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from AFO.config.settings import get_settings


def get_redis_client() -> redis.Redis:
    """
    동기 Redis 클라이언트 반환
    중앙 설정에서 Redis URL을 가져옴
    """
    settings = get_settings()
    redis_url = settings.get_redis_url()

    try:
        client = redis.from_url(redis_url)
        # 연결 테스트
        client.ping()
        return cast("redis.Redis", client)
    except Exception as e:
        raise ConnectionError(f"Redis 연결 실패: {e}") from e


async def get_async_redis_client() -> AsyncRedis:
    """
    비동기 Redis 클라이언트 반환
    중앙 설정에서 Redis URL을 가져옴
    """
    settings = get_settings()
    redis_url = settings.get_redis_url()

    try:
        client = AsyncRedis.from_url(redis_url)
        # 연결 테스트
        await client.ping()
        return cast("AsyncRedis", client)
    except Exception as e:
        raise ConnectionError(f"Redis 비동기 연결 실패: {e}") from e


def get_redis_url() -> str:
    """
    Redis URL 반환 (하위 호환성)
    """
    settings = get_settings()
    return settings.get_redis_url()


# 전역 Redis 클라이언트 (선택적, 연결 풀 관리용)
_redis_client: Redis | None = None
_async_redis_client: AsyncRedis | None = None


def get_shared_redis_client() -> redis.Redis:
    """
    공유 Redis 클라이언트 반환 (싱글톤)
    연결 풀을 재사용하여 성능 최적화
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client


async def get_shared_async_redis_client() -> AsyncRedis:
    """
    공유 비동기 Redis 클라이언트 반환 (싱글톤)
    """
    global _async_redis_client
    if _async_redis_client is None:
        _async_redis_client = await get_async_redis_client()
    return _async_redis_client


async def close_redis_connections() -> None:
    """
    Redis 연결 종료 (애플리케이션 종료 시 호출)

    Closes all Redis connections (sync and async).
    """
    global _redis_client, _async_redis_client

    if _redis_client:
        _redis_client.close()
        _redis_client = None

    if _async_redis_client:
        await _async_redis_client.close()
        _async_redis_client = None
