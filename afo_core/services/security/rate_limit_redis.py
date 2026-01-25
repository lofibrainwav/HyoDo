from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING, cast

from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from AFO.services.security.circuit_breaker import CircuitBreaker
from AFO.services.security.rate_limit_policy import RedisDownPolicy
from config.settings import settings

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI, Request

# Trinity Score: 90.0 (Established by Chancellor)


logger = logging.getLogger(__name__)


class RedisCircuitProbe:
    def __init__(
        self,
        redis_url: str,
        ttl_ms: int,
        timeout_ms: int,
        breaker: CircuitBreaker,
    ) -> None:
        self._redis_url = redis_url
        self._ttl = max(1, ttl_ms) / 1000.0
        self._timeout = max(1, timeout_ms) / 1000.0
        self._breaker = breaker

        self._last_check_at: float = 0.0
        self._last_ok: bool = True

        self._lock = asyncio.Lock()
        self._client: Redis | None = None

    async def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(self._redis_url)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def check(self) -> tuple[bool, str]:
        now = time.monotonic()

        async with self._lock:
            if not self._breaker.allow_probe(now):
                return False, self._breaker.state.value

            if (
                self._breaker.state.value == "CLOSED"
                and (now - self._last_check_at) < self._ttl
                and self._last_ok
            ):
                return True, self._breaker.state.value

            ok = False
            try:
                client = await self._get_client()
                await asyncio.wait_for(client.ping(), timeout=self._timeout)
                ok = True
            except Exception:
                ok = False

            self._last_check_at = time.monotonic()
            self._last_ok = ok

            if ok:
                self._breaker.record_success()
                return True, self._breaker.state.value

            self._breaker.record_failure(time.monotonic())
            return False, self._breaker.state.value


class RedisDownPolicyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        policy: RedisDownPolicy,
        probe: RedisCircuitProbe,
        on_warning: Callable[[Request, str], None] | None = None,
    ) -> None:
        super().__init__(app)
        self._policy = policy
        self._probe = probe
        self._on_warning = on_warning

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if self._policy.is_exempt(path):
            return cast("Response", await call_next(request))

        redis_ok, cb_state = await self._probe.check()
        if redis_ok:
            return cast("Response", await call_next(request))

        if self._policy.should_fail_closed(path):
            headers = {
                self._policy.warning_header_name: "1",
                self._policy.cb_state_header_name: cb_state,
                "Retry-After": os.getenv("AFO_REDIS_DOWN_RETRY_AFTER", "60").strip(),
            }
            return JSONResponse(
                status_code=self._policy.fail_closed_status,
                content={"detail": "redis_down"},
                headers=headers,
            )

        if self._on_warning is not None:
            self._on_warning(request, cb_state)

        response = cast("Response", await call_next(request))
        response.headers[self._policy.warning_header_name] = "1"
        response.headers[self._policy.cb_state_header_name] = cb_state
        return response


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return JSONResponse(status_code=429, content={"detail": "rate_limit_exceeded"})


def setup_redis_rate_limiter(app: FastAPI) -> None:
    redis_url = settings.get_redis_url()
    strategy = os.getenv("AFO_RATE_LIMIT_STRATEGY", "fixed-window").strip()
    default_limit = os.getenv("AFO_RATE_LIMIT_DEFAULT", "10/minute").strip()

    inmem_fallback_enabled = os.getenv(
        "AFO_RATE_LIMIT_INMEM_FALLBACK_ENABLED", "true"
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[default_limit],
        headers_enabled=True,
        storage_uri=redis_url,
        strategy=strategy,
        in_memory_fallback_enabled=inmem_fallback_enabled,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    policy = RedisDownPolicy.from_env()

    ttl_ms = int(os.getenv("AFO_REDIS_HEALTHCHECK_TTL_MS", "1000").strip())
    timeout_ms = int(os.getenv("AFO_REDIS_HEALTHCHECK_TIMEOUT_MS", "200").strip())

    cb_failure_threshold = int(os.getenv("AFO_REDIS_CB_FAILURE_THRESHOLD", "5").strip())
    cb_reset_timeout_s = float(os.getenv("AFO_REDIS_CB_RESET_TIMEOUT_S", "30").strip())
    cb_half_open_limit = int(os.getenv("AFO_REDIS_CB_HALF_OPEN_LIMIT", "2").strip())

    breaker = CircuitBreaker(
        failure_threshold=cb_failure_threshold,
        reset_timeout_s=cb_reset_timeout_s,
        half_open_limit=cb_half_open_limit,
    )

    probe = RedisCircuitProbe(
        redis_url=redis_url,
        ttl_ms=ttl_ms,
        timeout_ms=timeout_ms,
        breaker=breaker,
    )

    def _warn(req: Request, cb_state: str) -> None:
        logger.warning("redis_down path=%s cb_state=%s", req.url.path, cb_state)

    app.add_middleware(
        RedisDownPolicyMiddleware,  # type: ignore[arg-type]
        policy=policy,
        probe=probe,
        on_warning=_warn,
    )

    async def _shutdown() -> None:
        await probe.close()

    app.add_event_handler("shutdown", _shutdown)
