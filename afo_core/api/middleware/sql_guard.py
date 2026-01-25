from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from collections.abc import Iterable

    from starlette.requests import Request

# Trinity Score: 90.0 (Established by Chancellor)


_PATTERNS: Iterable[re.Pattern[str]] = (
    re.compile(r"(?i)\bunion\b\s+\bselect\b"),
    re.compile(r"(?i)\bor\b\s+1\s*=\s*1\b"),
    re.compile(r"(?i)\bdrop\b\s+\btable\b"),
    re.compile(r"(?i)\binsert\b\s+\binto\b"),
    re.compile(r"--"),
    re.compile(r"/\*"),
    re.compile(r";\s*$"),
)


def _mode() -> str:
    return os.getenv("AFO_SQL_GUARD_MODE", "log").lower()


def _is_suspicious_text(s: str) -> bool:
    if len(s) > 2000:
        return False
    return any(p.search(s) for p in _PATTERNS)


def _walk_strings(x: Any) -> Iterable[str]:
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for k, v in x.items():
            if isinstance(k, str):
                yield k
            yield from _walk_strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _walk_strings(v)


class SqlGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        mode = _mode()
        if mode == "off":
            return await call_next(request)  # type: ignore[no-any-return]

        suspicious = False

        for k, v in request.query_params.items():
            if _is_suspicious_text(k) or _is_suspicious_text(v):
                suspicious = True
                break

        if not suspicious and request.headers.get("content-type", "").startswith(
            "application/json"
        ):
            raw = await request.body()
            if raw and len(raw) <= 65536:
                try:
                    data = json.loads(raw.decode("utf-8"))
                    for s in _walk_strings(data):
                        if _is_suspicious_text(s):
                            suspicious = True
                            break
                except Exception:
                    pass

            async def _receive() -> dict:
                return {"type": "http.request", "body": raw, "more_body": False}

            request._receive = _receive

        if suspicious and mode == "block":
            return JSONResponse({"ok": False, "error": "suspicious_input"}, status_code=400)

        return await call_next(request)  # type: ignore[no-any-return]
