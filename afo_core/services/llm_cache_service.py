from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, cast

from pydantic import BaseModel, Field

from ..utils.redis_connection import get_redis_client

# Trinity Score: 90.0 (Established by Chancellor)
"""
LLM Cache Service for AFO Kingdom
High-performance caching for LLM requests/responses to reduce latency and API costs.

Sequential Thinking: 단계별 LLM 캐싱 시스템 구축
眞善美孝永: Truth 100%, Goodness 95%, Beauty 90%, Serenity 100%, Eternity 100%
"""


logger = logging.getLogger(__name__)

# 캐시 설정
LLM_CACHE_CONFIG = {
    "key_prefix": "llm:cache:",
    "default_ttl": 86400,  # 24시간
    "max_key_length": 250,  # Redis 키 길이 제한
    "compression_threshold": 1024,  # 1KB 이상 압축 고려
}


class LLMCacheEntry(BaseModel):
    """LLM 캐시 엔트리 모델"""

    request_hash: str = Field(..., description="요청 해시")
    provider: str = Field(..., description="LLM 제공자 (ollama, claude, gemini, openai)")
    model: str = Field(..., description="모델 이름")
    response: str = Field(..., description="LLM 응답")
    metadata: dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    created_at: float = Field(default_factory=time.time, description="생성 시간")
    ttl: int = Field(default=86400, description="TTL (초)")


class LLMCacheService:
    """
    LLM 응답 캐싱 서비스
    Sequential Thinking: 단계별 캐시 구현 및 최적화
    """

    def __init__(self) -> None:
        self.redis_client = None
        self._hit_count = 0
        self._miss_count = 0
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Redis 연결 초기화 (Sequential Thinking Phase 1)
        """
        try:
            self.redis_client = get_redis_client()
            if self.redis_client:
                # 연결 테스트
                self.redis_client.ping()
                self._initialized = True
                logger.info("✅ LLM Cache Service 초기화 완료")
                return True
            else:
                logger.warning("⚠️ Redis 클라이언트를 가져올 수 없습니다")
                return False
        except Exception as e:
            logger.warning(f"⚠️ LLM Cache Service 초기화 실패: {e}")
            self._initialized = False
            return False

    def _generate_cache_key(self, request_data: dict[str, Any], provider: str, model: str) -> str:
        """
        캐시 키 생성 (Sequential Thinking Phase 2)
        요청 데이터를 해시하여 고유 키 생성
        """
        # 요청 데이터 정규화 (순서 무관하게)
        normalized = {
            "provider": provider,
            "model": model,
            "messages": request_data.get("messages", []),
            "temperature": request_data.get("temperature"),
            "max_tokens": request_data.get("max_tokens"),
        }

        # JSON 직렬화 및 해시
        json_str = json.dumps(normalized, sort_keys=True)
        request_hash = hashlib.sha256(json_str.encode()).hexdigest()[:16]

        cache_key = f"{LLM_CACHE_CONFIG['key_prefix']}{provider}:{model}:{request_hash}"

        # Redis 키 길이 제한 확인
        if len(cache_key) > cast("int", LLM_CACHE_CONFIG["max_key_length"]):
            # 해시만 사용
            cache_key = f"{LLM_CACHE_CONFIG['key_prefix']}{request_hash}"

        return cache_key

    async def get_cached_response(
        self, request_data: dict[str, Any], provider: str, model: str
    ) -> str | None:
        """
        캐시에서 LLM 응답 조회 (Sequential Thinking Phase 3)
        """
        if not self._initialized or not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(request_data, provider, model)

            # Redis에서 조회
            cached_data = self.redis_client.get(cache_key)
            if cached_data is None:
                self._miss_count += 1
                logger.debug(f"LLM Cache Miss: {cache_key}")
                return None

            # JSON 역직렬화
            try:
                entry_dict = json.loads(cached_data)
                entry = LLMCacheEntry(**entry_dict)
                self._hit_count += 1
                logger.info(
                    f"✅ LLM Cache Hit: {cache_key} (saved {time.time() - entry.created_at:.1f}s ago)"
                )
                return entry.response
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"캐시 데이터 파싱 실패: {e}")
                # 손상된 캐시 삭제
                self.redis_client.delete(cache_key)
                return None

        except Exception as e:
            logger.error(f"LLM 캐시 조회 실패: {e}")
            return None

    async def cache_response(
        self,
        request_data: dict[str, Any],
        provider: str,
        model: str,
        response: str,
        metadata: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> bool:
        """
        LLM 응답을 캐시에 저장 (Sequential Thinking Phase 4)
        """
        if not self._initialized or not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(request_data, provider, model)
            ttl_value: int = (
                ttl if ttl is not None else cast("int", LLM_CACHE_CONFIG["default_ttl"])
            )

            # 캐시 엔트리 생성
            entry = LLMCacheEntry(
                request_hash=cache_key.split(":")[-1],
                provider=provider,
                model=model,
                response=response,
                metadata=metadata or {},
                ttl=ttl_value,
            )

            # JSON 직렬화 및 저장
            entry_json = json.dumps(entry.model_dump())
            self.redis_client.setex(cache_key, ttl_value, entry_json)

            logger.debug(f"✅ LLM Response Cached: {cache_key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"LLM 캐시 저장 실패: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """
        캐시 통계 조회
        """
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0.0

        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "total": total,
            "hit_rate": round(hit_rate, 2),
            "initialized": self._initialized,
        }

    async def clear_cache(self, pattern: str | None = None) -> int:
        """
        캐시 삭제 (선택적 패턴 매칭)
        """
        if not self._initialized or not self.redis_client:
            return 0

        try:
            pattern = pattern or f"{LLM_CACHE_CONFIG['key_prefix']}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"✅ LLM Cache Cleared: {deleted} keys deleted")
                return int(deleted)
            return 0
        except Exception as e:
            logger.error(f"캐시 삭제 실패: {e}")
            return 0


# 글로벌 인스턴스
_llm_cache_service: LLMCacheService | None = None


async def get_llm_cache_service() -> LLMCacheService:
    """
    LLM Cache Service 싱글톤 인스턴스 반환
    """
    global _llm_cache_service
    if _llm_cache_service is None:
        _llm_cache_service = LLMCacheService()
        await _llm_cache_service.initialize()
    return _llm_cache_service
