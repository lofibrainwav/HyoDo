# Trinity Score: 90.0 (Established by Chancellor)
"""
Test Configuration for AFO Kingdom
Provides test fixtures and mock implementations
"""

import pytest
from fastapi import APIRouter, FastAPI
from starlette.testclient import TestClient


def get_health_router() -> APIRouter:
    """Health router for testing"""
    router = APIRouter(prefix="/health", tags=["Health"])

    @router.get("")
    async def health_check():
        return {
            "status": "balanced",
            "service": "afo-test",
            "timestamp": "2026-01-21T00:00:00Z",
            "version": "1.0.0",
            "trinity_metrics": {
                "balance_status": "balanced",
                "trinity_score": 92.5,
                "decision": "AUTO_RUN",
            },
        }

    @router.get("/ping")
    async def health_ping():
        return {"status": "ok", "service": "afo-test"}

    return router


def get_system_router() -> APIRouter:
    """System router for testing"""
    router = APIRouter(prefix="/api/system", tags=["System"])

    @router.get("/health")
    async def system_health():
        return {
            "status": "balanced",
            "timestamp": "2026-01-21T00:00:00Z",
            "version": "1.0.0",
            "service": "afo-test",
        }

    return router


def create_test_app() -> FastAPI:
    """Create test FastAPI app with routers"""
    app = FastAPI(title="AFO Kingdom Test API")
    app.include_router(get_health_router())
    app.include_router(get_system_router())
    return app


# Create test app instance
app = create_test_app()


@pytest.fixture
def client() -> TestClient:
    """Test client fixture"""
    with TestClient(app) as c:
        yield c
