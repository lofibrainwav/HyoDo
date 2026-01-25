from __future__ import annotations

import asyncio
import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""Redis 최적화 모듈 - Pipeline + Lua Script 통합
AFO Ascension Protocol - Phase 1.1

기능:
- Redis Pipeline 배치 처리
- Lua Script 서버 측 실행 (GET-OR-COMPUTE 패턴)
- Async Redis 클라이언트 지원
- 캐시 히트율 모니터링
"""


class OptimizedRedisCache:
    """최적화된 Redis 캐시 클래스
    Pipeline + Lua Script + 모니터링 통합
    """

    def __init__(self, client: Any | None = None) -> None:
        self.client = client
        self.hit_count = 0
        self.miss_count = 0
        self.pipeline_count = 0

        # Lua Script 등록 (GET-OR-COMPUTE 패턴)
        self._register_lua_scripts()

    def _register_lua_scripts(self) -> None:
        """Lua 스크립트 등록"""
        if not self.client:
            return

        # GET-OR-COMPUTE 스크립트
        self.get_or_compute_script = self.client.register_script(
            """
            local key = KEYS[1]
            local ttl = ARGV[1]

            -- 캐시 확인
            local cached = redis.call('GET', key)
            if cached then
                return {'hit', cached}
            end

            -- 없으면 placeholder 설정 후 miss 반환
            redis.call('SETEX', key, ttl, '__COMPUTING__')
            return {'miss', ''}
        """
        )

        # 배치 GET 스크립트
        self.batch_get_script = self.client.register_script(
            """
            local results = {}
            for i, key in ipairs(KEYS) do
                local value = redis.call('GET', key)
                if value and value ~= '__COMPUTING__' then
                    results[i] = value
                else
                    results[i] = false
                end
            end
            return results
        """
        )

    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable[..., Any],
        ttl_seconds: int = 300,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """GET-OR-COMPUTE 패턴 구현

        Args:
            key: 캐시 키
            compute_func: 계산 함수 (async)
            ttl_seconds: TTL 초
            *args, **kwargs: compute_func에 전달할 인자

        Returns:
            계산된 값

        """
        if not self.client:
            # Redis 없으면 직접 계산
            return await compute_func(*args, **kwargs)

        try:
            # Lua Script 실행
            result = await self.get_or_compute_script(keys=[key], args=[ttl_seconds])

            if result[0] == "hit":
                self.hit_count += 1
                return json.loads(result[1])

            # MISS - 계산 수행
            self.miss_count += 1
            value = await compute_func(*args, **kwargs)

            # 캐시에 저장
            await self.client.setex(key, ttl_seconds, json.dumps(value))
            return value

        except Exception as e:
            print(f"Redis GET-OR-COMPUTE 실패: {e}")
            # 실패 시 직접 계산
            return await compute_func(*args, **kwargs)

    async def batch_get(self, keys: list[str]) -> dict[str, Any]:
        """배치 GET 작업

        Args:
            keys: 키 리스트

        Returns:
            {key: value} 딕셔너리

        """
        if not self.client:
            return {}

        try:
            # Lua Script로 배치 조회
            results = await self.batch_get_script(keys=keys)

            self.pipeline_count += 1
            sum(1 for r in results if r is not False)

            return {
                key: json.loads(value) if value is not False else None
                for key, value in zip(keys, results, strict=False)
            }

        except Exception as e:
            print(f"Redis 배치 GET 실패: {e}")
            return {}

    async def batch_set(self, key_values: dict[str, Any], ttl_seconds: int = 300) -> None:
        """배치 SET 작업

        Args:
            key_values: {key: value} 딕셔너리
            ttl_seconds: TTL 초

        """
        if not self.client:
            return

        try:
            async with self.client.pipeline() as pipe:
                for key, value in key_values.items():
                    pipe.setex(key, ttl_seconds, json.dumps(value))
                await pipe.execute()
                self.pipeline_count += 1

        except Exception as e:
            print(f"Redis 배치 SET 실패: {e}")

    def get_stats(self) -> dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "pipeline_count": self.pipeline_count,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


# 전역 캐시 인스턴스
_redis_cache: OptimizedRedisCache | None = None


def get_redis_cache(client: Any | None = None) -> OptimizedRedisCache:
    """전역 Redis 캐시 인스턴스 반환"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = OptimizedRedisCache(client)
    return _redis_cache


# 편의 함수들
async def cached_get_or_compute(
    key: str,
    compute_func: Callable[..., Any],
    ttl_seconds: int = 300,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """편의 함수 - 캐시된 GET-OR-COMPUTE"""
    """편의 함수 - 캐시된 GET-OR-COMPUTE"""
    cache = get_redis_cache()
    return await cache.get_or_compute(key, compute_func, ttl_seconds, *args, **kwargs)


async def cached_batch_get(keys: list[str]) -> dict[str, Any]:
    """편의 함수 - 캐시된 배치 GET"""
    cache = get_redis_cache()
    return await cache.batch_get(keys)


async def cached_batch_set(key_values: dict[str, Any], ttl_seconds: int = 300) -> None:
    """편의 함수 - 캐시된 배치 SET"""
    cache = get_redis_cache()
    return await cache.batch_set(key_values, ttl_seconds)


def get_cache_stats() -> dict[str, Any]:
    """편의 함수 - 캐시 통계 조회"""
    cache = get_redis_cache()
    return cache.get_stats()


# 캐시 키 생성 헬퍼
def make_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """표준화된 캐시 키 생성"""
    key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()


if __name__ == "__main__":
    # 테스트
    async def test_compute(x: int) -> int:
        await asyncio.sleep(0.1)  # 계산 시뮬레이션
        return x * 2

    async def main() -> None:
        print("🧪 Redis 최적화 모듈 테스트 시작...")

        # 캐시 인스턴스 생성 (Redis 연결 없이 테스트)
        OptimizedRedisCache()

        # GET-OR-COMPUTE 테스트
        print("📊 GET-OR-COMPUTE 테스트...")
        result1 = await cached_get_or_compute("test:1", test_compute, 60, 5)
        result2 = await cached_get_or_compute("test:1", test_compute, 60, 5)  # 캐시 히트

        print(f"✅ 결과 1: {result1}")
        print(f"✅ 결과 2 (캐시): {result2}")

        # 통계 출력
        stats = get_cache_stats()
        print(f"📈 캐시 통계: {stats}")

        print("🎉 Redis 최적화 모듈 테스트 완료!")

    asyncio.run(main())
