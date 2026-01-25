# Trinity Score: 93.0 (Phase 33 Audit Module Refactoring)
"""FastAPI Integration - Middleware and Setup Functions"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response

from .trail import get_audit_trail

logger = logging.getLogger(__name__)


# ============================================================================
# FastAPI Middleware (孝 - Serenity)
# ============================================================================


async def audit_middleware(request: Request, call_next) -> Response:
    """FastAPI middleware for HTTP request auditing

    Logs all HTTP requests with timing, user info, and response status.
    Integrates with the global audit trail.
    """
    # Generate trace ID if not present
    trace_id = getattr(request.state, "trace_id", None)
    if not trace_id:
        trace_id = str(uuid.uuid4())[:12]
        request.state.trace_id = trace_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Skip logging for health checks and static files
        skip_paths = {"/health", "/healthz", "/metrics", "/favicon.ico"}
        if request.url.path not in skip_paths:
            # Extract user info from request state if available
            user_id = getattr(request.state, "user_id", None)
            api_key_name = getattr(request.state, "api_key_name", None)

            audit_trail = get_audit_trail()
            await audit_trail.log_http_request(
                request,
                response,
                duration_ms,
                user_id=user_id,
                api_key_name=api_key_name,
            )

        return response

    except Exception as e:
        # Log error
        duration_ms = (time.perf_counter() - start_time) * 1000

        audit_trail = get_audit_trail()
        await audit_trail.log(
            event_type=AuditEventType.SYSTEM_ERROR,
            action=f"Request failed: {request.method} {request.url.path}",
            severity=AuditSeverity.ERROR,
            trace_id=trace_id,
            client_ip=AuditTrail._get_client_ip(request),
            http_method=request.method,
            http_path=request.url.path,
            duration_ms=duration_ms,
            success=False,
            error_message=str(e),
        )

        raise


# ============================================================================
# Setup Functions (孝 - Serenity)
# ============================================================================


def setup_audit(app: FastAPI) -> None:
    """Setup audit middleware on FastAPI app

    Args:
        app: FastAPI application instance
    """
    app.middleware("http")(audit_middleware)
    logger.info("AFO Audit Trail middleware initialized (眞善美孝永)")


# ============================================================================
# Legacy Compatibility Imports (孝 - Serenity)
# ============================================================================

# Import for backward compatibility
from .models import AuditEventType, AuditSeverity
from .trail import AuditTrail
