"""
Redis 기반 분산 Rate Limiting 엔진

Goodness 기둥 강화: 분산 레이트 리미팅으로 리스크 최소화
- Redis 기반 분산 카운터 (Single Point of Failure 방지)
- Sliding Window 알고리즘 (고정 윈도우보다 정확)
- 자동 만료 및 메모리 효율성 최적화
"""

import json
import time
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis

from config.settings import settings


@dataclass
class RateLimitConfig:
    """Rate Limiting 설정"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "burst_limit": self.burst_limit,
            "window_seconds": self.window_seconds,
        }


@dataclass
class RateLimitResult:
    """Rate Limiting 결과"""

    allowed: bool
    remaining_requests: int
    reset_time: float
    retry_after: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "remaining_requests": self.remaining_requests,
            "reset_time": self.reset_time,
            "retry_after": self.retry_after,
        }


class DistributedRateLimiter:
    """
    Redis 기반 분산 Rate Limiting 엔진

    특징:
    - Sliding Window: 고정 윈도우보다 정확한 제한
    - 분산 안전: Redis로 Single Point of Failure 방지
    - 메모리 효율: 자동 만료로 메모리 누수 방지
    - Burst 허용: 급격한 요청 증가 대응
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "ratelimit:",
        config: RateLimitConfig | None = None,
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.config = config or RateLimitConfig()

    async def check_rate_limit(
        self,
        key: str,
        cost: int = 1,
        custom_config: RateLimitConfig | None = None,
    ) -> RateLimitResult:
        """
        Rate Limit 체크

        Args:
            key: 고유 식별자 (IP, User ID, API Key 등)
            cost: 요청 비용 (일반적으로 1)
            custom_config: 사용자 정의 설정 (없으면 기본값 사용)

        Returns:
            RateLimitResult: 허용 여부와 남은 요청 수
        """
        config = custom_config or self.config
        now = time.time()

        # Redis 키 생성
        window_key = f"{self.key_prefix}{key}:window"
        burst_key = f"{self.key_prefix}{key}:burst"

        try:
            # Pipeline으로 원자적 연산
            async with self.redis.pipeline() as pipe:
                # Sliding Window 체크
                pipe.zremrangebyscore(window_key, 0, now - config.window_seconds)
                pipe.zcard(window_key)
                pipe.zadd(window_key, {str(now): now})
                pipe.expire(window_key, config.window_seconds * 2)  # 안전 마진

                # Burst 체크
                pipe.incr(burst_key)
                pipe.expire(burst_key, 60)  # 1분 TTL

                results = await pipe.execute()

            current_requests = results[1]  # zcard 결과
            burst_count = results[4]  # incr 결과

            # Rate Limit 판정
            minute_limit_exceeded = current_requests >= config.requests_per_minute
            burst_limit_exceeded = burst_count > config.burst_limit

            if minute_limit_exceeded or burst_limit_exceeded:
                # 제한 초과: 재시도 시간 계산
                reset_time = now + config.window_seconds
                retry_after = config.window_seconds

                # Burst 카운터 감소 (롤백)
                await self.redis.decr(burst_key)

                return RateLimitResult(
                    allowed=False,
                    remaining_requests=0,
                    reset_time=reset_time,
                    retry_after=retry_after,
                )

            # 허용: 남은 요청 수 계산
            remaining_minute = max(0, config.requests_per_minute - current_requests)
            remaining_burst = max(0, config.burst_limit - burst_count)

            return RateLimitResult(
                allowed=True,
                remaining_requests=min(remaining_minute, remaining_burst),
                reset_time=now + config.window_seconds,
            )

        except Exception as e:
            # Redis 오류 시 관대하게 허용 (Fail Open)
            print(f"Rate limiting error: {e}")
            return RateLimitResult(
                allowed=True,
                remaining_requests=self.config.requests_per_minute,
                reset_time=now + self.config.window_seconds,
            )

    async def get_rate_limit_status(self, key: str) -> dict[str, Any]:
        """
        현재 Rate Limit 상태 조회

        Args:
            key: 고유 식별자

        Returns:
            현재 상태 정보
        """
        window_key = f"{self.key_prefix}{key}:window"
        burst_key = f"{self.key_prefix}{key}:burst"

        try:
            async with self.redis.pipeline() as pipe:
                pipe.zcard(window_key)
                pipe.get(burst_key)
                pipe.ttl(window_key)
                results = await pipe.execute()

            current_requests = results[0] or 0
            burst_count = int(results[1] or 0)
            ttl = results[2] or 0

            return {
                "current_requests": current_requests,
                "burst_count": burst_count,
                "ttl": ttl,
                "config": self.config.to_dict(),
            }
        except Exception as e:
            return {"error": str(e)}

    async def reset_rate_limit(self, key: str) -> bool:
        """
        Rate Limit 리셋 (관리자용)

        Args:
            key: 리셋할 식별자

        Returns:
            성공 여부
        """
        try:
            window_key = f"{self.key_prefix}{key}:window"
            burst_key = f"{self.key_prefix}{key}:burst"

            await self.redis.delete(window_key, burst_key)
            return True
        except Exception:
            return False


# FastAPI 미들웨어용 헬퍼
class RateLimitMiddleware:
    """
    FastAPI 미들웨어용 Rate Limiting 헬퍼

    사용법:
        limiter = DistributedRateLimiter(redis_client)
        middleware = RateLimitMiddleware(limiter)

        # 미들웨어에서 사용
        result = await middleware.check_request(client_ip)
        if not result.allowed:
            raise HTTPException(429, "Rate limit exceeded")
    """

    def __init__(self, limiter: DistributedRateLimiter) -> None:
        self.limiter = limiter

    async def check_request(
        self,
        identifier: str,
        cost: int = 1,
        custom_config: RateLimitConfig | None = None,
    ) -> RateLimitResult:
        """
        요청 체크

        Args:
            identifier: 클라이언트 식별자 (IP, User ID 등)
            cost: 요청 비용
            custom_config: 사용자 정의 설정

        Returns:
            RateLimitResult
        """
        return await self.limiter.check_rate_limit(identifier, cost, custom_config)

    def create_dependency(self, key_func: Any = None) -> None:
        """
        FastAPI Dependency 생성

        Args:
            key_func: 키 생성 함수 (없으면 IP 사용)

        Returns:
            FastAPI dependency 함수
        """

        async def rate_limit_dependency(request):
            from fastapi import HTTPException

            # 키 생성
            if key_func:
                key = key_func(request)
            else:
                # 기본: 클라이언트 IP
                key = getattr(request.client, "host", "unknown") if request.client else "unknown"

            # Rate Limit 체크
            result = await self.check_request(key)

            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Remaining": str(result.remaining_requests),
                        "X-RateLimit-Reset": str(int(result.reset_time)),
                        "Retry-After": str(int(result.retry_after or 60)),
                    },
                )

            # 허용: 헤더 추가
            request.state.rate_limit_remaining = result.remaining_requests
            request.state.rate_limit_reset = result.reset_time

            return result

        return rate_limit_dependency


# Secret Zero 정책 구현
class SecretZeroGuard:
    """
    Secret Zero 정책 엔진

    모든 환경에서 시크릿 노출을 0으로 유지:
    - 환경 변수 스캔
    - 코드 정적 분석
    - 런타임 검증
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client
        self.secret_patterns = [
            r"(?i)(Union[Union[password, passwd], Union][pwd, secret]|Union[Union[key, token], auth])",
            r"(?i)(Union[aws_access_key, aws_secret_key])",
            r"(?i)(Union[database_url, db_url])",
            r"(?i)(Union[openai_api_key, anthropic_api_key])",
        ]

    async def scan_for_secrets(self, content: str, source: str) -> list[str]:
        """
        콘텐츠에서 시크릿 패턴 스캔

        Args:
            content: 스캔할 콘텐츠
            source: 출처 정보

        Returns:
            발견된 시크릿 목록
        """
        import re

        found_secrets = []
        for pattern in self.secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_secrets.extend([f"{source}:{match}" for match in matches])

        return found_secrets

    async def validate_environment(self) -> dict[str, Any]:
        """
        환경 변수 검증

        Returns:
            검증 결과
        """
        import os

        results = {"safe": True, "violations": []}

        for key, value in os.environ.items():
            is_sensitive = any(
                pattern in key.lower() for pattern in ["secret", "key", "token", "password"]
            )
            if is_sensitive and len(value) > 10:  # 의미 있는 값이 있는 경우
                results["violations"].append(f"Environment variable: {key}")
                results["safe"] = False

        return results

    async def log_security_event(self, event: str, details: dict[str, Any]) -> None:
        """
        보안 이벤트 로깅

        Args:
            event: 이벤트 유형
            details: 이벤트 세부 정보
        """
        try:
            log_entry = {
                "event": event,
                "details": details,
                "timestamp": time.time(),
            }

            await self.redis.lpush("security_events", json.dumps(log_entry))
            await self.redis.ltrim("security_events", 0, 999)  # 최근 1000개만 유지

        except Exception as e:
            print(f"Security logging error: {e}")


# 전역 인스턴스
_default_rate_limiter = None
_secret_guard = None


async def get_rate_limiter() -> DistributedRateLimiter:
    """전역 Rate Limiter 인스턴스"""
    global _default_rate_limiter
    if _default_rate_limiter is None:
        # Redis 클라이언트 생성 (환경 변수에서 설정)

        redis_url = settings.get_redis_url()
        redis_client = redis.from_url(redis_url)
        _default_rate_limiter = DistributedRateLimiter(redis_client)
    return _default_rate_limiter


async def get_secret_guard() -> SecretZeroGuard:
    """전역 Secret Guard 인스턴스"""
    global _secret_guard
    if _secret_guard is None:
        redis_url = settings.get_redis_url()
        redis_client = redis.from_url(redis_url)
        _secret_guard = SecretZeroGuard(redis_client)
    return _secret_guard
