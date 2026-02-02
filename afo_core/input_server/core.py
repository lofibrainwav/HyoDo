# Trinity Score: 94.0 (Phase 30 Core Refactoring)
"""Input Server Core - FastAPI Application Setup"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    AddKeyResponse,
    BulkImportResponse,
    add_api_key,
    api_add_key,
    api_bulk_import,
    api_status,
    bulk_import,
    get_history,
    health_check,
    home_page,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="AFO Input Server",
        description="API 키 입력 및 관리 서버 (胃 Stomach)",
        version="1.0.0",
    )

    # CORS 미들웨어 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발 환경용 - 프로덕션에서는 제한
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 엔드포인트 등록
    app.get("/health")(health_check)
    app.get("/")(home_page)
    app.post("/add_key")(add_api_key)
    app.get("/api/status")(api_status)
    app.post("/bulk_import")(bulk_import)
    app.get("/api/history")(get_history)

    # JSON-based API endpoints (RESTful)
    app.post("/api/add_key", response_model=AddKeyResponse)(api_add_key)
    app.post("/api/bulk_import", response_model=BulkImportResponse)(api_bulk_import)

    return app


# Global app instance
app = create_app()
