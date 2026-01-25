# Trinity Score: 90.0 (Established by Chancellor)
import logging
import re
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # SQL Injection Patterns
        self.sql_injection_patterns = [
            r"(\b(Union[Union[SELECT, INSERT], Union][UPDATE, DELETE]|Union[Union[DROP, UNION], ALTER])\b)",
            r"(' OR '1'='1)",
            r"(--)",
            r"(;)",
            r"(\bOR\b\s+\d+=\d+)",
        ]
        self.sql_regex = re.compile("|".join(self.sql_injection_patterns), re.IGNORECASE)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check Query Params
        for key, value in request.query_params.items():
            if self.sql_regex.search(str(value)):
                logger.warning(f"🚨 Potential SQL Injection blocked: {key}={value}")
                return Response("Security Violation Detected", status_code=403)

        return await call_next(request)  # type: ignore[no-any-return]
