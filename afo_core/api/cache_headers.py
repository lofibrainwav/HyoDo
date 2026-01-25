# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/api/cache_headers.py
# (Cache-Control Headers Optimization - PDF 성능 최적화 기반)
# 🧭 Trinity Score: 眞90% 善95% 美95% 孝95%

import hashlib
import logging
from typing import Literal

from fastapi import Request, Response

logger = logging.getLogger(__name__)

CACHE_STRATEGIES = {
    "static": "public, max-age=31536000, immutable",  # 정적 자산 (영속)
    "dynamic": "private, max-age=0, no-cache, stale-while-revalidate=60",  # 동적 (SWR Short)
    "realtime": "private, max-age=60, stale-while-revalidate=300",  # 실시간 Data (SWR Long)
    "sensitive": "private, no-store",  # 민감 (No Cache)
}


def set_optimized_cache_headers(
    response: Response,
    asset_type: Literal["static", "dynamic", "realtime", "sensitive"],
) -> None:
    """Cache-Control Headers Optimization: 자산 유형별 최적 헤더

    Args:
        response: FastAPI Response object
        asset_type: Strategy name ('static', 'dynamic', 'realtime', 'sensitive')

    """
    strategy = CACHE_STRATEGIES.get(asset_type, CACHE_STRATEGIES["dynamic"])

    response.headers["Cache-Control"] = strategy

    # Modern CDNs often respect this header for edge caching separate from browser
    if asset_type != "sensitive":
        response.headers["CDN-Cache-Control"] = strategy

    logger.debug(f"[Cache-Control] Applied strategy '{asset_type}': {strategy}")


def set_etag_and_cache(
    response: Response,
    content: bytes,
    asset_type: Literal["static", "dynamic", "realtime", "sensitive"],
) -> None:
    """ETag + Cache-Control 결합 최적화
    Generates ETag from content and applies cache headers.
    """
    # 1. Generate ETag (Strong validation)
    etag = hashlib.md5(content, usedforsecurity=False).hexdigest()
    response.headers["ETag"] = f'"{etag}"'

    # 2. Set Cache-Control
    set_optimized_cache_headers(response, asset_type)

    logger.debug(f"[ETag] Generated: {etag}")


def check_etag_match(request: Request, current_content: bytes) -> bool:
    """Checks if client's If-None-Match header matches current content hash.
    Returns True if valid (should return 304), False otherwise.
    """
    client_etag = request.headers.get("If-None-Match")
    if not client_etag:
        return False

    current_etag = hashlib.md5(current_content, usedforsecurity=False).hexdigest()
    # Handle quoted etags
    return client_etag.strip('"') == current_etag
