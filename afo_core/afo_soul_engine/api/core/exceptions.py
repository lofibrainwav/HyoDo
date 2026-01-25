from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request

# Trinity Score: 90.0 (Established by Chancellor)


class AFOException(Exception):
    """Base domain exception for API error handling."""

    def __init__(self, message: str, *, status_code: int = 400, detail: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


def afo_exception_handler(_request: Request, exc: AFOException) -> Response:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "AFOException", "message": str(exc), "detail": exc.detail},
    )


def http_exception_handler(_request: Request, exc: Exception) -> Response:
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", str(exc))
    return JSONResponse(
        status_code=status_code, content={"error": "HTTPException", "detail": detail}
    )


def validation_exception_handler(_request: Request, exc: Exception) -> Response:
    status_code = getattr(exc, "status_code", 422)
    errors_attr = getattr(exc, "errors", None)
    # FastAPI's RequestValidationError.errors is a method, call it if callable
    errors = errors_attr() if callable(errors_attr) else errors_attr
    return JSONResponse(
        status_code=status_code,
        content={
            "error": "ValidationError",
            "detail": getattr(exc, "detail", str(exc)),
            "errors": errors,
        },
    )


def general_exception_handler(_request: Request, exc: Exception) -> Response:
    return JSONResponse(
        status_code=500, content={"error": "UnhandledException", "detail": str(exc)}
    )
