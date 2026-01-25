from __future__ import annotations

import os
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request

# Trinity Score: 90.0 (Established by Chancellor)


def _max_body_bytes() -> int:
    v = os.getenv("AFO_MAX_BODY_BYTES", "1048576")
    try:
        return max(1024, int(v))
    except Exception:
        return 1048576


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > _max_body_bytes():
                    return JSONResponse(
                        {"ok": False, "error": "payload_too_large"}, status_code=413
                    )
            except Exception:
                return JSONResponse(
                    {"ok": False, "error": "invalid_content_length"}, status_code=400
                )
        return await call_next(request)  # type: ignore[no-any-return]
