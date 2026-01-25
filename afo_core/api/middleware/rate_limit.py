from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request

# Trinity Score: 90.0 (Established by Chancellor)


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


def _enabled() -> bool:
    return os.getenv("AFO_RATE_LIMIT_ENABLED", "true").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _key_from_request(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
        if ip:
            return ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@dataclass
class _Bucket:
    tokens: float
    last: float


class InMemoryRateLimiter:
    def __init__(self, rps: int, burst: int) -> None:
        self.rps = max(1, rps)
        self.burst = max(1, burst)
        self._lock = asyncio.Lock()
        self._buckets: dict[str, _Bucket] = {}

    async def allow(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        async with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = _Bucket(tokens=float(self.burst), last=now)
                self._buckets[key] = b
            elapsed = max(0.0, now - b.last)
            b.last = now
            b.tokens = min(float(self.burst), b.tokens + elapsed * float(self.rps))
            if b.tokens >= 1.0:
                b.tokens -= 1.0
                return True, int(b.tokens)
            return False, int(b.tokens)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.enabled = _enabled()
        self.rps = _env_int("AFO_RATE_LIMIT_RPS", 10)
        self.burst = _env_int("AFO_RATE_LIMIT_BURST", 20)
        self._limiter = InMemoryRateLimiter(self.rps, self.burst)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)  # type: ignore[no-any-return]

        path = request.url.path
        if path in ("/health", "/"):
            return await call_next(request)  # type: ignore[no-any-return]

        key = _key_from_request(request)
        ok, remaining = await self._limiter.allow(key)
        if not ok:
            return JSONResponse({"ok": False, "error": "rate_limited"}, status_code=429)

        resp = await call_next(request)
        resp.headers["x-ratelimit-limit-rps"] = str(self.rps)
        resp.headers["x-ratelimit-burst"] = str(self.burst)
        resp.headers["x-ratelimit-remaining"] = str(max(0, remaining))
        return resp  # type: ignore[no-any-return]
