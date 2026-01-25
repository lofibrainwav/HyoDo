# Trinity Score: 93.0 (永 - Eternal Persistence)
"""Redis-backed Strategist Registry.

Redis를 사용한 Strategist Registry 영속화.
분산 환경에서 일관된 에이전트 상태를 유지합니다.

AFO 철학:
- 永 (Eternity): 상태 영속화
- 孝 (Serenity): 분산 환경 조화
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from redis.asyncio import Redis as AsyncRedis

    from ..sub_agents.base_strategist import BaseStrategist

logger = logging.getLogger(__name__)


@dataclass
class StrategistMetadata:
    """Strategist 메타데이터 (Redis 저장용)."""

    pillar: str
    name_ko: str
    name_en: str
    weight: float
    scholar_key: str

    # 상태
    registered_at: float = field(default_factory=time.time)
    last_active_at: float = 0.0
    evaluation_count: int = 0
    error_count: int = 0

    # 성능 메트릭
    avg_duration_ms: float = 0.0
    avg_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "pillar": self.pillar,
            "name_ko": self.name_ko,
            "name_en": self.name_en,
            "weight": self.weight,
            "scholar_key": self.scholar_key,
            "registered_at": self.registered_at,
            "last_active_at": self.last_active_at,
            "evaluation_count": self.evaluation_count,
            "error_count": self.error_count,
            "avg_duration_ms": self.avg_duration_ms,
            "avg_score": self.avg_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategistMetadata:
        """딕셔너리에서 생성."""
        return cls(
            pillar=data.get("pillar", ""),
            name_ko=data.get("name_ko", ""),
            name_en=data.get("name_en", ""),
            weight=data.get("weight", 0.0),
            scholar_key=data.get("scholar_key", ""),
            registered_at=data.get("registered_at", time.time()),
            last_active_at=data.get("last_active_at", 0.0),
            evaluation_count=data.get("evaluation_count", 0),
            error_count=data.get("error_count", 0),
            avg_duration_ms=data.get("avg_duration_ms", 0.0),
            avg_score=data.get("avg_score", 0.0),
        )

    @classmethod
    def from_strategist(cls, strategist: BaseStrategist) -> StrategistMetadata:
        """Strategist 인스턴스에서 생성."""
        return cls(
            pillar=strategist.PILLAR,
            name_ko=strategist.NAME_KO,
            name_en=strategist.NAME_EN,
            weight=strategist.WEIGHT,
            scholar_key=strategist.SCHOLAR_KEY,
        )


class RedisStrategistRegistry:
    """Redis 기반 Strategist Registry.

    Usage:
        registry = RedisStrategistRegistry()
        await registry.connect()

        # 등록
        await registry.register("truth", jang_yeong_sil_agent)

        # 조회
        metadata = await registry.get_metadata("truth")

        # 상태 업데이트
        await registry.record_evaluation("truth", score=0.85, duration_ms=150)
    """

    REDIS_KEY_PREFIX = "afo:strategist:"
    METADATA_KEY = "afo:strategist:metadata"
    ACTIVE_KEY = "afo:strategist:active"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: int = 3600,
    ) -> None:
        """Registry 초기화.

        Args:
            redis_url: Redis 연결 URL
            ttl_seconds: 메타데이터 TTL
        """
        self._redis_url = redis_url
        self._ttl = ttl_seconds
        self._redis: AsyncRedis | None = None
        self._local_cache: dict[str, StrategistMetadata] = {}
        self._strategists: dict[str, BaseStrategist] = {}
        self._connected = False

    async def connect(self) -> bool:
        """Redis 연결."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            self._connected = True
            logger.info(f"Redis registry connected: {self._redis_url}")
            return True
        except ImportError:
            logger.warning("redis package not installed, using local cache only")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using local cache")
            return False

    async def disconnect(self) -> None:
        """Redis 연결 해제."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    async def register(
        self,
        pillar: str,
        strategist: BaseStrategist,
    ) -> StrategistMetadata:
        """Strategist 등록.

        Args:
            pillar: Pillar 이름
            strategist: Strategist 인스턴스

        Returns:
            생성된 메타데이터
        """
        pillar_lower = pillar.lower()
        metadata = StrategistMetadata.from_strategist(strategist)

        # 로컬 저장
        self._strategists[pillar_lower] = strategist
        self._local_cache[pillar_lower] = metadata

        # Redis 저장
        if self._connected and self._redis:
            try:
                key = f"{self.REDIS_KEY_PREFIX}{pillar_lower}"
                await self._redis.hset(key, mapping=metadata.to_dict())
                await self._redis.expire(key, self._ttl)

                # 활성 목록에 추가
                await self._redis.sadd(self.ACTIVE_KEY, pillar_lower)

                logger.debug(f"Strategist registered in Redis: {pillar_lower}")
            except Exception as e:
                logger.warning(f"Redis registration failed: {e}")

        return metadata

    async def unregister(self, pillar: str) -> bool:
        """Strategist 등록 해제.

        Args:
            pillar: Pillar 이름

        Returns:
            해제 성공 여부
        """
        pillar_lower = pillar.lower()

        # 로컬 제거
        self._strategists.pop(pillar_lower, None)
        self._local_cache.pop(pillar_lower, None)

        # Redis 제거
        if self._connected and self._redis:
            try:
                key = f"{self.REDIS_KEY_PREFIX}{pillar_lower}"
                await self._redis.delete(key)
                await self._redis.srem(self.ACTIVE_KEY, pillar_lower)
            except Exception as e:
                logger.warning(f"Redis unregistration failed: {e}")

        return True

    def get(self, pillar: str) -> BaseStrategist | None:
        """Strategist 인스턴스 조회 (동기)."""
        return self._strategists.get(pillar.lower())

    async def get_metadata(self, pillar: str) -> StrategistMetadata | None:
        """Strategist 메타데이터 조회.

        Args:
            pillar: Pillar 이름

        Returns:
            메타데이터 또는 None
        """
        pillar_lower = pillar.lower()

        # Redis에서 먼저 시도
        if self._connected and self._redis:
            try:
                key = f"{self.REDIS_KEY_PREFIX}{pillar_lower}"
                data = await self._redis.hgetall(key)
                if data:
                    # 숫자 필드 변환
                    for field in [
                        "weight",
                        "registered_at",
                        "last_active_at",
                        "evaluation_count",
                        "error_count",
                        "avg_duration_ms",
                        "avg_score",
                    ]:
                        if field in data:
                            data[field] = float(data[field])
                    metadata = StrategistMetadata.from_dict(data)
                    self._local_cache[pillar_lower] = metadata
                    return metadata
            except Exception as e:
                logger.debug(f"Redis metadata fetch failed: {e}")

        # 로컬 캐시 폴백
        return self._local_cache.get(pillar_lower)

    async def record_evaluation(
        self,
        pillar: str,
        score: float,
        duration_ms: float,
        error: bool = False,
    ) -> None:
        """평가 결과 기록.

        Args:
            pillar: Pillar 이름
            score: 평가 점수
            duration_ms: 소요 시간 (ms)
            error: 에러 발생 여부
        """
        pillar_lower = pillar.lower()
        metadata = await self.get_metadata(pillar_lower)

        if not metadata:
            return

        # 통계 업데이트
        metadata.last_active_at = time.time()
        metadata.evaluation_count += 1
        if error:
            metadata.error_count += 1

        # 이동 평균 업데이트
        alpha = 0.1
        metadata.avg_duration_ms = (1 - alpha) * metadata.avg_duration_ms + alpha * duration_ms
        metadata.avg_score = (1 - alpha) * metadata.avg_score + alpha * score

        # 저장
        self._local_cache[pillar_lower] = metadata

        if self._connected and self._redis:
            try:
                key = f"{self.REDIS_KEY_PREFIX}{pillar_lower}"
                await self._redis.hset(key, mapping=metadata.to_dict())
            except Exception as e:
                logger.debug(f"Redis evaluation record failed: {e}")

    async def get_active_pillars(self) -> list[str]:
        """활성 Pillar 목록 조회."""
        if self._connected and self._redis:
            try:
                return list(await self._redis.smembers(self.ACTIVE_KEY))
            except Exception:
                pass
        return list(self._strategists.keys())

    async def get_all_metadata(self) -> dict[str, StrategistMetadata]:
        """모든 Strategist 메타데이터 조회."""
        result = {}
        pillars = await self.get_active_pillars()

        for pillar in pillars:
            metadata = await self.get_metadata(pillar)
            if metadata:
                result[pillar] = metadata

        return result

    async def health_check(self) -> dict[str, Any]:
        """상태 확인."""
        redis_ok = False
        if self._connected and self._redis:
            try:
                await self._redis.ping()
                redis_ok = True
            except Exception:
                pass

        return {
            "redis_connected": redis_ok,
            "local_cache_size": len(self._local_cache),
            "strategists_loaded": len(self._strategists),
            "active_pillars": list(self._strategists.keys()),
        }

    def get_status(self) -> dict[str, Any]:
        """레지스트리 상태 조회 (동기)."""
        return {
            "redis_url": self._redis_url,
            "connected": self._connected,
            "ttl_seconds": self._ttl,
            "local_cache": {pillar: meta.to_dict() for pillar, meta in self._local_cache.items()},
        }


# 싱글톤 인스턴스
_default_registry: RedisStrategistRegistry | None = None


async def get_redis_registry() -> RedisStrategistRegistry:
    """기본 Redis Registry 조회."""
    global _default_registry
    if _default_registry is None:
        _default_registry = RedisStrategistRegistry()
        await _default_registry.connect()
    return _default_registry
