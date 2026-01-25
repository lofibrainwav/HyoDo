# Trinity Score: 90.0 (Established by Chancellor)
"""
Redis Cache Service for AFO Kingdom (Phase 9)
High-performance Redis-based caching with monitoring and optimization.
Sequential Thinking: 단계별 캐시 시스템 구축 및 최적화
"""

import json
import logging
import time
from typing import Any

import redis
from pydantic import BaseModel, Field

from ..utils.circuit_breaker import CircuitBreaker
from ..utils.exponential_backoff import exponential_backoff

# 로깅 설정
logger = logging.getLogger(__name__)


# Phase 35-1: 하드코딩 제거 - settings 객체에서 설정 가져오기
def _get_redis_config() -> dict[str, Any]:
    """settings 객체에서 Redis 설정을 가져오는 함수"""
    try:
        from AFO.config.settings import settings

        return {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": 0,
            "decode_responses": True,
            "socket_connect_timeout": settings.REDIS_TIMEOUT,
            "socket_timeout": settings.REDIS_TIMEOUT,
            "retry_on_timeout": True,
            "max_connections": settings.REDIS_MAX_CONNECTIONS,
            "password": settings.REDIS_PASSWORD,
        }
    except ImportError:
        # Fallback: 하드코딩 값 사용 (호환성 유지)
        return {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
            "max_connections": 20,
        }


def _get_cache_config() -> dict[str, Any]:
    """settings 객체에서 캐시 설정을 가져오는 함수"""
    try:
        from AFO.config.settings import settings

        return {
            "default_ttl": settings.CACHE_DEFAULT_TTL,
            "max_memory_mb": settings.MAX_MEMORY_MB,
            "compression_threshold": 1024,  # 1KB 이상 압축
            "key_prefix": "afo:",
            "monitoring_enabled": True,
        }
    except ImportError:
        # Fallback: 하드코딩 값 사용 (호환성 유지)
        return {
            "default_ttl": 3600,  # 1시간
            "max_memory_mb": 512.0,  # 512MB
            "compression_threshold": 1024,  # 1KB 이상 압축
            "key_prefix": "afo:",
            "monitoring_enabled": True,
        }


REDIS_CONFIG = _get_redis_config()
CACHE_CONFIG = _get_cache_config()


class CacheStats(BaseModel):
    """캐시 통계 모델"""

    total_keys: int = Field(default=0, description="전체 키 수")
    memory_used_mb: float = Field(default=0.0, description="사용 메모리 (MB)")
    hit_rate: float = Field(default=0.0, description="히트율 (%)")
    miss_rate: float = Field(default=0.0, description="미스율 (%)")
    evictions: int = Field(default=0, description="퇴출된 키 수")
    connections: int = Field(default=0, description="활성 연결 수")
    uptime_seconds: int = Field(default=0, description="업타임 (초)")


class CacheEntry(BaseModel):
    """캐시 엔트리 모델"""

    key: str
    value: Any
    ttl: int | None = None
    created_at: float = Field(default_factory=time.time)
    access_count: int = Field(default=0)
    last_accessed: float | None = None
    size_bytes: int = Field(default=0)


class RedisCacheService:
    """
    Redis Cache Service with advanced features and monitoring.
    Sequential Thinking: 단계별 캐시 구현 및 최적화
    """

    def __init__(self) -> None:
        self.redis_client: Any | None = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exceptions=(redis.ConnectionError, redis.TimeoutError),
            service_name="redis_cache",
        )
        self._stats = CacheStats()
        self._start_time = time.time()
        self._hit_count = 0
        self._miss_count = 0

    async def initialize(self) -> bool:
        """
        Redis 연결 초기화 (Sequential Thinking Phase 1)
        """
        try:
            # Phase 1.1: Redis 클라이언트 생성
            self.redis_client = redis.Redis(**REDIS_CONFIG)

            # Phase 1.2: 연결 테스트
            if self.redis_client is not None:
                redis_client = self.redis_client  # 타입 가드
                await exponential_backoff(
                    lambda: redis_client.ping(), max_retries=3, base_delay=1.0
                )

            # Phase 1.3: 메모리 제한 설정
            max_memory_mb_val = CACHE_CONFIG["max_memory_mb"]
            max_memory_mb: float = (
                float(max_memory_mb_val)
                if isinstance(max_memory_mb_val, (int, float, str))
                else 512.0
            )
            max_memory_bytes: int = int(max_memory_mb * 1024 * 1024)  # type: ignore[arg-type]
            self.redis_client.config_set("maxmemory", str(max_memory_bytes))
            self.redis_client.config_set("maxmemory-policy", "allkeys-lru")

            logger.info("✅ Redis 캐시 서비스 초기화 완료")
            return True

        except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
            logger.error(
                "❌ Redis 캐시 서비스 초기화 실패 (연결/타임아웃/시스템 에러): %s",
                str(e),
            )
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("❌ Redis 캐시 서비스 초기화 실패 (예상치 못한 에러): %s", str(e))
            return False

    @property
    def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

    async def set(
        self, key: str, value: Any, ttl: int | None = None, compress: bool = True
    ) -> bool:
        """
        캐시에 값 저장 (Sequential Thinking Phase 2)
        """
        if not self.redis_client or not self.is_connected:
            logger.warning("Redis 연결 없음 - 캐시 저장 생략")
            return False

        try:
            # Phase 2.1: 키 생성
            cache_key = f"{CACHE_CONFIG['key_prefix']}{key}"

            # Phase 2.2: 값 직렬화
            serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

            # Phase 2.3: 압축 적용 (선택적)
            final_value = serialized_value
            compression_threshold: int = int(CACHE_CONFIG["compression_threshold"])
            if compress and len(serialized_value) > compression_threshold:
                # 간단한 압축 로직 (실제 구현에서는 더 정교한 압축 사용)
                final_value = f"compressed:{serialized_value}"

            # Phase 2.4: TTL 설정
            default_ttl_val = CACHE_CONFIG["default_ttl"]
            default_ttl: int = (
                int(default_ttl_val) if isinstance(default_ttl_val, (int, str)) else 3600
            )
            effective_ttl: int = ttl if ttl is not None else default_ttl

            # Phase 2.5: Redis 저장
            # 이미 위에서 self.redis_client None 체크 완료
            redis_client = self.redis_client  # 타입 가드
            success_result = await exponential_backoff(
                lambda: redis_client.setex(cache_key, effective_ttl, final_value),
                max_retries=2,
            )
            success: bool = bool(success_result) if success_result is not None else False

            if success:
                logger.debug(f"캐시 저장: {cache_key} (TTL: {effective_ttl}s)")
                self._update_stats(set_operation=True)

            return success

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error("캐시 저장 실패 (연결/타임아웃 에러, 키: %s): %s", key, str(e))
            return False
        except (TypeError, ValueError) as e:
            logger.error("캐시 저장 실패 (타입/값/JSON 직렬화 에러, 키: %s): %s", key, str(e))
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("캐시 저장 실패 (예상치 못한 에러, 키: %s): %s", key, str(e))
            return False

    async def get(self, key: str) -> Any | None:
        """
        캐시에서 값 조회 (Sequential Thinking Phase 3)
        """
        if not self.redis_client or not self.is_connected:
            logger.debug("Redis 연결 없음 - 캐시 조회 생략")
            return None

        try:
            # Phase 3.1: 키 생성
            cache_key = f"{CACHE_CONFIG['key_prefix']}{key}"

            # Phase 3.2: Redis 조회
            # 이미 위에서 self.redis_client None 체크 완료
            redis_client = self.redis_client  # 타입 가드
            value = await exponential_backoff(lambda: redis_client.get(cache_key), max_retries=2)

            if value is None:
                # 캐시 미스
                self._miss_count += 1
                return None

            # Phase 3.3: 값 역직렬화
            if isinstance(value, str):
                if value.startswith("compressed:"):
                    # 압축 해제 (실제 구현에서는 압축 해제 로직)
                    value = value[11:]  # "compressed:" 제거

                try:
                    # JSON 파싱 시도
                    deserialized = json.loads(value)
                except json.JSONDecodeError:
                    # 일반 문자열
                    deserialized = value
            else:
                deserialized = value

            # Phase 3.4: 통계 업데이트
            self._hit_count += 1
            self._update_stats(get_operation=True)

            logger.debug(f"캐시 히트: {cache_key}")
            return deserialized

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error("캐시 조회 실패 (연결/타임아웃 에러, 키: %s): %s", key, str(e))
            self._miss_count += 1
            return None
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error("캐시 조회 실패 (JSON 파싱/타입/값 에러, 키: %s): %s", key, str(e))
            self._miss_count += 1
            return None
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("캐시 조회 실패 (예상치 못한 에러, 키: %s): %s", key, str(e))
            self._miss_count += 1
            return None

    async def delete(self, key: str) -> bool:
        """
        캐시에서 키 삭제 (Sequential Thinking Phase 4)
        """
        if not self.redis_client or not self.is_connected:
            return False

        try:
            cache_key = f"{CACHE_CONFIG['key_prefix']}{key}"
            # 이미 위에서 self.redis_client None 체크 완료
            redis_client = self.redis_client  # 타입 가드
            delete_result = await exponential_backoff(
                lambda: redis_client.delete(cache_key), max_retries=2
            )
            success: bool = bool(delete_result) if delete_result is not None else False

            if success:
                logger.debug(f"캐시 삭제: {cache_key}")
                self._update_stats(delete_operation=True)

            return success

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error("캐시 삭제 실패 (연결/타임아웃 에러, 키: %s): %s", key, str(e))
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("캐시 삭제 실패 (예상치 못한 에러, 키: %s): %s", key, str(e))
            return False

    async def clear_all(self) -> bool:
        """
        모든 캐시 삭제 (Sequential Thinking Phase 5)
        """
        if not self.redis_client or not self.is_connected:
            return False

        try:
            # 패턴 매칭으로 AFO 키들만 삭제
            # 이미 위에서 self.redis_client None 체크 완료
            redis_client = self.redis_client  # 타입 가드
            keys_result = redis_client.keys(f"{CACHE_CONFIG['key_prefix']}*")
            keys: list[str] = list(keys_result) if isinstance(keys_result, list) else []

            if keys:
                delete_result = await exponential_backoff(
                    lambda: redis_client.delete(*keys), max_retries=2
                )
                success: bool = bool(delete_result) if delete_result is not None else False

                if success:
                    logger.info(f"전체 캐시 정리: {len(keys)}개 키 삭제")
                    self._update_stats(clear_operation=len(keys))

                return success

            return True

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error("전체 캐시 정리 실패 (연결/타임아웃 에러): %s", str(e))
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("전체 캐시 정리 실패 (예상치 못한 에러): %s", str(e))
            return False

    async def get_stats(self) -> CacheStats:
        """
        캐시 통계 조회 (Sequential Thinking Phase 6)
        """
        if not self.redis_client or not self.is_connected:
            return CacheStats()

        try:
            # Phase 6.1: Redis 정보 조회
            redis_client = self.redis_client  # 타입 가드
            info_result = redis_client.info()
            info: dict[str, Any] = (
                info_result
                if isinstance(info_result, dict)
                else await exponential_backoff(
                    lambda: info_result if isinstance(info_result, dict) else {},
                    max_retries=2,
                )
            )

            # Phase 6.2: 메모리 정보 조회
            memory_result = redis_client.memory_stats()
            memory_info: dict[str, Any] = (
                memory_result
                if isinstance(memory_result, dict)
                else await exponential_backoff(
                    lambda: memory_result if isinstance(memory_result, dict) else {},
                    max_retries=2,
                )
            )

            # Phase 6.3: 키 카운트
            keys_result = self.redis_client.keys(f"{CACHE_CONFIG['key_prefix']}*")
            key_count: int = len(keys_result) if isinstance(keys_result, list) else 0

            # Phase 6.4: 통계 계산
            total_requests = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0.0
            miss_rate = (self._miss_count / total_requests * 100) if total_requests > 0 else 0.0

            memory_used_bytes = memory_info.get("total.allocated", 0)
            memory_used_mb = memory_used_bytes / (1024 * 1024)

            stats = CacheStats(
                total_keys=key_count,
                memory_used_mb=round(memory_used_mb, 2),
                hit_rate=round(hit_rate, 2),
                miss_rate=round(miss_rate, 2),
                evictions=info.get("evicted_keys", 0),
                connections=info.get("connected_clients", 0),
                uptime_seconds=int(time.time() - self._start_time),
            )

            return stats

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error("캐시 통계 조회 실패 (연결/타임아웃 에러): %s", str(e))
            return CacheStats()
        except (AttributeError, KeyError, TypeError) as e:
            logger.error("캐시 통계 조회 실패 (속성/키/타입 에러): %s", str(e))
            return CacheStats()
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("캐시 통계 조회 실패 (예상치 못한 에러): %s", str(e))
            return CacheStats()

    async def health_check(self) -> dict[str, Any]:
        """
        건강 상태 점검 (Sequential Thinking Phase 7)
        """
        health_status: dict[str, Any] = {
            "service": "redis_cache",
            "status": "unknown",
            "details": {},
            "timestamp": time.time(),
        }
        details: dict[str, Any] = health_status["details"]

        try:
            # Phase 7.1: 연결 상태 확인
            is_connected = self.is_connected
            details["connection"] = "healthy" if is_connected else "unhealthy"

            if is_connected:
                # Phase 7.2: 기본 동작 테스트
                test_key = f"{CACHE_CONFIG['key_prefix']}health_check_{int(time.time())}"

                # 쓰기 테스트
                write_success = await self.set(test_key, "test_value", ttl=10)
                details["write_test"] = "passed" if write_success else "failed"

                # 읽기 테스트
                read_value = await self.get(test_key)
                read_success = read_value == "test_value"
                details["read_test"] = "passed" if read_success else "failed"

                # 정리
                await self.delete(test_key)

                # Phase 7.3: 성능 메트릭
                stats = await self.get_stats()
                details["stats"] = stats.model_dump()

                # Phase 7.4: 종합 상태 판정
                if write_success and read_success:
                    health_status["status"] = "healthy"
                else:
                    health_status["status"] = "degraded"
            else:
                health_status["status"] = "unhealthy"

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error("건강 상태 점검 실패 (연결/타임아웃 에러): %s", str(e))
            health_status["status"] = "error"
            details["error"] = str(e)
        except (AttributeError, KeyError, TypeError) as e:
            logger.error("건강 상태 점검 실패 (속성/키/타입 에러): %s", str(e))
            health_status["status"] = "error"
            details["error"] = str(e)
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("건강 상태 점검 실패 (예상치 못한 에러): %s", str(e))
            health_status["status"] = "error"
            details["error"] = str(e)

        return health_status

    def _update_stats(
        self,
        set_operation: bool = False,
        get_operation: bool = False,
        delete_operation: bool = False,
        clear_operation: int = 0,
    ) -> None:
        """
        내부 통계 업데이트 (Sequential Thinking Phase 8)
        """
        try:
            if set_operation:
                self._stats.total_keys += 1
            elif get_operation:
                pass  # 히트율은 별도 계산
            elif delete_operation:
                self._stats.total_keys = max(0, self._stats.total_keys - 1)
            elif clear_operation > 0:
                self._stats.total_keys = max(0, self._stats.total_keys - clear_operation)

        except (AttributeError, TypeError) as e:
            logger.debug("통계 업데이트 실패 (속성/타입 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("통계 업데이트 실패 (예상치 못한 에러): %s", str(e))


# 전역 인스턴스
redis_cache_service = RedisCacheService()


async def get_cache_service() -> RedisCacheService:
    """캐시 서비스 인스턴스 반환"""
    return redis_cache_service


async def initialize_cache_service() -> bool:
    """캐시 서비스 초기화"""
    return await redis_cache_service.initialize()


# 편의 함수들
async def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    """캐시 설정 편의 함수"""
    return await redis_cache_service.set(key, value, ttl)


async def cache_get(key: str) -> Any | None:
    """캐시 조회 편의 함수"""
    return await redis_cache_service.get(key)


async def cache_delete(key: str) -> bool:
    """캐시 삭제 편의 함수"""
    return await redis_cache_service.delete(key)


async def cache_clear() -> bool:
    """캐시 전체 삭제 편의 함수"""
    return await redis_cache_service.clear_all()


async def get_cache_stats() -> CacheStats:
    """캐시 통계 조회 편의 함수"""
    return await redis_cache_service.get_stats()
