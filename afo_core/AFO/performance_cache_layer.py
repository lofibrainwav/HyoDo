"""
Performance Cache Layer - Phase 1+2 성능 최적화

AI 응답 캐싱, 데이터베이스 쿼리 캐싱, 메모리 최적화
Redis 기반 고성능 캐싱 시스템
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import redis.asyncio as redis
from pydantic import BaseModel


class CacheConfig(BaseModel):
    """캐시 설정 모델"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 20

    # 캐시 TTL 설정
    ai_response_ttl: int = 1800  # 30분
    db_query_ttl: int = 300  # 5분
    chart_data_ttl: int = 600  # 10분
    voice_response_ttl: int = 3600  # 1시간


class CacheKey:
    """캐시 키 생성 유틸리티"""

    @staticmethod
    def ai_response(client_id: str, query_hash: str, model: str) -> str:
        """AI 응답 캐시 키"""
        return f"ai:{client_id}:{query_hash}:{model}"

    @staticmethod
    def db_query(query_hash: str, params_hash: str) -> str:
        """데이터베이스 쿼리 캐시 키"""
        return f"db:{query_hash}:{params_hash}"

    @staticmethod
    def chart_data(client_id: str, chart_type: str, data_hash: str) -> str:
        """차트 데이터 캐시 키"""
        return f"chart:{client_id}:{chart_type}:{data_hash}"

    @staticmethod
    def voice_command(command_hash: str, context_hash: str) -> str:
        """음성 명령 캐시 키"""
        return f"voice:{command_hash}:{context_hash}"

    @staticmethod
    def create_hash(data: Any) -> str:
        """데이터 해시 생성"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode()).hexdigest()[:16]


class PerformanceCacheLayer:
    """
    고성능 캐시 레이어

    Phase 1+2 성능 최적화의 핵심 컴포넌트
    Redis 기반 다중 레벨 캐싱 구현
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        self.config = config or CacheConfig()
        self.redis_client: redis.Redis | None = None
        self._local_cache: dict[str, dict[str, Any]] = {}  # L1 캐시 (메모리)
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}

    async def initialize(self):
        """캐시 레이어 초기화"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                max_connections=self.config.max_connections,
                decode_responses=False,  # 바이너리 데이터 지원
            )

            # 연결 테스트
            await self.redis_client.ping()
            print("✅ Performance Cache Layer: Redis 연결 성공")

        except Exception as e:
            print(f"❌ Performance Cache Layer 초기화 실패: {e}")
            # Redis 실패 시 L1 캐시만 사용
            self.redis_client = None

    async def close(self):
        """캐시 레이어 종료"""
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Any | None:
        """캐시에서 데이터 조회 (다중 레벨)"""

        # L1 캐시 확인
        if key in self._local_cache:
            l1_data = self._local_cache[key]
            if datetime.now() < l1_data["expires_at"]:
                self._stats["hits"] += 1
                return l1_data["data"]
            else:
                # 만료된 L1 캐시 제거
                del self._local_cache[key]

        # L2 캐시 (Redis) 확인
        if self.redis_client:
            try:
                data = await self.redis_client.get(key)
                if data is not None:
                    # L1 캐시에 저장
                    deserialized_data = pickle.loads(data)  # noqa: S301
                    self._set_l1_cache(key, deserialized_data)
                    self._stats["hits"] += 1
                    return deserialized_data
            except Exception as e:
                self._stats["errors"] += 1
                print(f"Redis 캐시 조회 오류: {e}")

        self._stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        """캐시에 데이터 저장"""

        try:
            # L1 캐시에 저장
            self._set_l1_cache(key, value, ttl_seconds)

            # L2 캐시 (Redis)에 저장
            if self.redis_client:
                serialized_data = pickle.dumps(value)
                await self.redis_client.setex(key, ttl_seconds or 300, serialized_data)

            self._stats["sets"] += 1
            return True

        except Exception as e:
            self._stats["errors"] += 1
            print(f"캐시 저장 오류: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""

        try:
            # L1 캐시에서 삭제
            if key in self._local_cache:
                del self._local_cache[key]

            # L2 캐시에서 삭제
            if self.redis_client:
                await self.redis_client.delete(key)

            self._stats["deletes"] += 1
            return True

        except Exception as e:
            self._stats["errors"] += 1
            print(f"캐시 삭제 오류: {e}")
            return False

    def _set_l1_cache(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """L1 캐시에 데이터 저장"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds or 300)
        self._local_cache[key] = {"data": value, "expires_at": expires_at}

    async def get_ai_response(
        self, client_id: str, query: str, model: str
    ) -> dict[str, Any] | None:
        """AI 응답 캐시 조회"""
        query_hash = CacheKey.create_hash(query)
        cache_key = CacheKey.ai_response(client_id, query_hash, model)

        cached_response = await self.get(cache_key)
        if cached_response:
            print(f"🎯 캐시 히트: AI 응답 ({model})")
        return cached_response

    async def set_ai_response(
        self, client_id: str, query: str, model: str, response: dict[str, Any]
    ):
        """AI 응답 캐시 저장"""
        query_hash = CacheKey.create_hash(query)
        cache_key = CacheKey.ai_response(client_id, query_hash, model)

        await self.set(cache_key, response, self.config.ai_response_ttl)
        print(f"💾 AI 응답 캐시 저장: {model} ({self.config.ai_response_ttl}초)")

    async def get_db_query(self, query: str, params: dict[str, Any]) -> Any | None:
        """데이터베이스 쿼리 결과 캐시 조회"""
        query_hash = CacheKey.create_hash(query)
        params_hash = CacheKey.create_hash(params)
        cache_key = CacheKey.db_query(query_hash, params_hash)

        cached_result = await self.get(cache_key)
        if cached_result:
            print("🎯 캐시 히트: DB 쿼리 결과")
        return cached_result

    async def set_db_query(self, query: str, params: dict[str, Any], result: Any):
        """데이터베이스 쿼리 결과 캐시 저장"""
        query_hash = CacheKey.create_hash(query)
        params_hash = CacheKey.create_hash(params)
        cache_key = CacheKey.db_query(query_hash, params_hash)

        await self.set(cache_key, result, self.config.db_query_ttl)
        print(f"💾 DB 쿼리 캐시 저장 ({self.config.db_query_ttl}초)")

    async def get_chart_data(
        self, client_id: str, chart_type: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """차트 데이터 캐시 조회"""
        data_hash = CacheKey.create_hash(data)
        cache_key = CacheKey.chart_data(client_id, chart_type, data_hash)

        cached_chart = await self.get(cache_key)
        if cached_chart:
            print(f"🎯 캐시 히트: 차트 데이터 ({chart_type})")
        return cached_chart

    async def set_chart_data(
        self, client_id: str, chart_type: str, data: dict[str, Any], chart_result: dict[str, Any]
    ):
        """차트 데이터 캐시 저장"""
        data_hash = CacheKey.create_hash(data)
        cache_key = CacheKey.chart_data(client_id, chart_type, data_hash)

        await self.set(cache_key, chart_result, self.config.chart_data_ttl)
        print(f"💾 차트 데이터 캐시 저장: {chart_type} ({self.config.chart_data_ttl}초)")

    async def get_voice_command(
        self, command: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """음성 명령 캐시 조회"""
        command_hash = CacheKey.create_hash(command)
        context_hash = CacheKey.create_hash(context)
        cache_key = CacheKey.voice_command(command_hash, context_hash)

        cached_response = await self.get(cache_key)
        if cached_response:
            print("🎯 캐시 히트: 음성 명령 응답")
        return cached_response

    async def set_voice_command(
        self, command: str, context: dict[str, Any], response: dict[str, Any]
    ):
        """음성 명령 캐시 저장"""
        command_hash = CacheKey.create_hash(command)
        context_hash = CacheKey.create_hash(context)
        cache_key = CacheKey.voice_command(command_hash, context_hash)

        await self.set(cache_key, response, self.config.voice_response_ttl)
        print(f"💾 음성 명령 캐시 저장 ({self.config.voice_response_ttl}초)")

    async def clear_expired_cache(self):
        """만료된 캐시 정리 (L1 캐시)"""
        current_time = datetime.now()
        expired_keys = [
            key for key, data in self._local_cache.items() if current_time >= data["expires_at"]
        ]

        for key in expired_keys:
            del self._local_cache[key]

        if expired_keys:
            print(f"🧹 만료된 L1 캐시 정리: {len(expired_keys)}개 항목")

    async def get_cache_stats(self) -> dict[str, Any]:
        """캐시 통계 조회"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        redis_info = {}
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info()
            except Exception:
                redis_info = {"error": "Redis 연결 실패"}

        return {
            "cache_stats": {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "deletes": self._stats["deletes"],
                "errors": self._stats["errors"],
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
            },
            "l1_cache": {
                "items_count": len(self._local_cache),
                "config": {
                    "ai_response_ttl": self.config.ai_response_ttl,
                    "db_query_ttl": self.config.db_query_ttl,
                    "chart_data_ttl": self.config.chart_data_ttl,
                    "voice_response_ttl": self.config.voice_response_ttl,
                },
            },
            "redis_status": "connected" if self.redis_client else "disconnected",
            "redis_info": redis_info,
        }

    async def health_check(self) -> dict[str, Any]:
        """캐시 레이어 건강 상태 확인"""
        health_status = {
            "overall_health": "healthy",
            "l1_cache": "healthy",
            "redis": "unknown",
            "checks": {},
        }

        # L1 캐시 건강 확인
        try:
            l1_items = len(self._local_cache)
            health_status["checks"]["l1_cache_items"] = l1_items
        except Exception as e:
            health_status["l1_cache"] = "unhealthy"
            health_status["checks"]["l1_cache_error"] = str(e)

        # Redis 건강 확인
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health_status["redis"] = "healthy"
                health_status["checks"]["redis_ping"] = "success"
            except Exception as e:
                health_status["redis"] = "unhealthy"
                health_status["checks"]["redis_error"] = str(e)
        else:
            health_status["redis"] = "disconnected"

        # 전반적 건강 상태 결정
        if health_status["l1_cache"] == "unhealthy":
            health_status["overall_health"] = "degraded"
        if health_status["redis"] == "unhealthy":
            health_status["overall_health"] = "critical"

        return health_status


# 데코레이터: 함수 결과 자동 캐싱
def cached(
    cache_layer: PerformanceCacheLayer, ttl_seconds: int = 300, key_prefix: str = ""
) -> None:
    """함수 결과 자동 캐싱 데코레이터"""

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            func_name = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            args_hash = CacheKey.create_hash({"args": args, "kwargs": kwargs})
            cache_key = f"func:{func_name}:{args_hash}"

            # 캐시 조회
            cached_result = await cache_layer.get(cache_key)
            if cached_result is not None:
                print(f"🎯 함수 캐시 히트: {func.__name__}")
                return cached_result

            # 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            await cache_layer.set(cache_key, result, ttl_seconds)
            print(f"💾 함수 결과 캐시 저장: {func.__name__}")

            return result

        return wrapper

    return decorator


# 글로벌 캐시 인스턴스
_performance_cache = None


async def get_performance_cache() -> PerformanceCacheLayer:
    """글로벌 캐시 인스턴스 획득"""
    global _performance_cache

    if _performance_cache is None:
        _performance_cache = PerformanceCacheLayer()
        await _performance_cache.initialize()

    return _performance_cache


async def initialize_performance_cache():
    """성능 캐시 레이어 초기화"""
    cache = await get_performance_cache()
    print("🚀 Performance Cache Layer 초기화 완료")
    return cache


async def shutdown_performance_cache():
    """성능 캐시 레이어 종료"""
    global _performance_cache

    if _performance_cache:
        await _performance_cache.close()
        _performance_cache = None
        print("🛑 Performance Cache Layer 종료 완료")
