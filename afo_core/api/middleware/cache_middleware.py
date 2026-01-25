# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO API Cache Middleware
Redis-based caching for optimal response times.
"""

import hashlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, cast

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

# 중앙 설정 및 유틸리티

logger = logging.getLogger(__name__)

# 캐시 설정
API_CACHE_CONFIG: dict[str, Any] = {
    "ttl": 300,  # 5분
    "key_prefix": "afo:api:cache:",
    "cacheable_status_codes": [200],
}


class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.redis_client: Any = None
        self._hit_count = 0
        self._miss_count = 0
        self._initialized = False
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """Initialize Redis cache with retry logic (善: Graceful degradation)"""
        if self._initialized:
            return

        max_retries = 3
        retry_delay = 0.5  # seconds

        for attempt in range(max_retries):
            try:
                from AFO.utils.redis_connection import get_redis_client

                client = get_redis_client()
                if client is not None:
                    client.ping()
                    self.redis_client = client
                    self._initialized = True
                    logger.debug("✅ API Cache Middleware 초기화 완료 (attempt %d)", attempt + 1)
                    return
            except Exception as e:
                if attempt < max_retries - 1:
                    import time

                    time.sleep(retry_delay * (attempt + 1))
                    logger.warning(
                        "⚠️ Redis 연결 재시도 중... (attempt %d/%d)",
                        attempt + 1,
                        max_retries,
                    )
                else:
                    logger.warning("⚠️ API Cache 비활성화 (Redis 없이 정상 작동): %s", e)

        # Graceful fallback - cache disabled but app continues
        self.redis_client = None
        self._initialized = False

    def _generate_cache_key(self, request: Request) -> str:
        path = request.url.path
        query_string = str(request.url.query)
        query_hash = hashlib.md5(query_string.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{API_CACHE_CONFIG['key_prefix']}{request.method}:{path}:{query_hash}"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self._initialized or request.method != "GET":
            return await call_next(request)

        url_path = str(request.url.path)
        if "/health" in url_path and "/comprehensive" not in url_path:
            return await call_next(request)

        # SSE Stream Bypass (Critical: Do not buffer infinite streams)
        if "stream" in url_path or "logs" in url_path:
            return await call_next(request)

        cache_key = self._generate_cache_key(request)

        if self.redis_client is not None:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    try:
                        cache_entry = json.loads(cached_data)
                        self._hit_count += 1
                        hit_response = JSONResponse(
                            content=cache_entry["body"],
                            status_code=cache_entry["status_code"],
                        )
                        hit_response.headers["X-Cache"] = "HIT"
                        hit_response.headers["X-Cache-Key"] = cache_key
                        if url_path == "/api/health/comprehensive":
                            hit_response.headers["Cache-Control"] = "max-age=30, private"
                            hit_response.headers["X-Cache-Source"] = "server-cache"
                        return hit_response
                    except Exception:
                        self.redis_client.delete(cache_key)
            except Exception:
                pass

        self._miss_count += 1
        miss_response: Response = await call_next(request)

        cacheable_codes = cast("list[int]", API_CACHE_CONFIG["cacheable_status_codes"])
        if (
            self._initialized
            and self.redis_client is not None
            and miss_response.status_code in cacheable_codes
        ):
            try:
                response_body = b""
                if hasattr(miss_response, "body_iterator"):
                    async for chunk in cast("Any", miss_response).body_iterator:
                        response_body += chunk
                    try:
                        body_json = json.loads(response_body.decode())
                        cache_entry = {
                            "body": body_json,
                            "status_code": miss_response.status_code,
                            "timestamp": time.time(),
                        }
                        self.redis_client.setex(
                            cache_key, API_CACHE_CONFIG["ttl"], json.dumps(cache_entry)
                        )
                        final_response = JSONResponse(
                            content=body_json,
                            status_code=miss_response.status_code,
                            headers=dict(miss_response.headers),
                        )
                        final_response.headers["X-Cache"] = "MISS"
                        final_response.headers["X-Cache-Key"] = cache_key
                        return final_response
                    except Exception:
                        return Response(
                            content=response_body,
                            status_code=miss_response.status_code,
                            headers=dict(miss_response.headers),
                        )
            except Exception:
                pass
        return miss_response

    def get_stats(self) -> dict[str, Any]:
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": round(hit_rate, 2),
            "initialized": self._initialized,
        }
