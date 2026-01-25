# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom API Middleware Configuration

Handles CORS, security, monitoring, and other middleware setup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the FastAPI application."""
    # Cache middleware (Phase 1.2: API 엔드포인트 캐싱)
    _setup_cache_middleware(app)

    # Performance monitoring middleware (Phase 3.1: 성능 모니터링)
    _setup_performance_middleware(app)

    # Security middleware (audit logging)
    _setup_security_middleware(app)

    # Monitoring middleware (Prometheus)
    _setup_monitoring_middleware(app)

    # CORS middleware (Must be added last to run first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8010",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8010",
        ],  # Explicit origins for credentials support
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _setup_security_middleware(app: FastAPI) -> None:
    """Setup security-related middleware."""
    try:
        from AFO.api.middleware.audit import audit_middleware
        from AFO.api.middleware.security import SecurityMiddleware
        from AFO.security.vault_manager import vault

        # Security Middleware (SQL Injection Check) - First Line of Defense
        app.add_middleware(SecurityMiddleware)

        # Audit Middleware (Before Routes)
        app.middleware("http")(audit_middleware)

        # Initialize Vault (Log only)
        print(f"🛡️ Vault Manager Active (Mode: {vault.mode})")
        print("🛡️ Audit Middleware Active (Logging POST/PUT/DELETE)")

    except Exception as e:
        print(f"⚠️ Security Hardening 설정 실패: {e}")

    # Phase 2 Hardening: Add security middleware stack
    _setup_phase2_hardening_middleware(app)


def _setup_phase2_hardening_middleware(app: FastAPI) -> None:
    """Setup Phase 2 Hardening security middleware stack."""
    try:
        # Import Phase 2 Hardening middleware
        from AFO.api.middleware.rate_limit_redis import (
            create_rate_limit_middleware,
            create_redis_limiter,
        )
        from AFO.api.middleware.request_limits import RequestSizeLimitMiddleware
        from AFO.api.middleware.sql_guard import SqlGuardMiddleware
        from AFO.api.middleware.trace_id import TraceIdMiddleware

        # Add middleware in correct order (most permissive to most restrictive)
        app.add_middleware(TraceIdMiddleware)
        app.add_middleware(RequestSizeLimitMiddleware)

        # Redis-backed rate limiting (distributed support)
        redis_limiter = create_redis_limiter()
        rate_limit_middleware = create_rate_limit_middleware(redis_limiter)
        if rate_limit_middleware is not None:
            app.add_middleware(rate_limit_middleware)

        app.add_middleware(SqlGuardMiddleware)

        print("🛡️ Phase 2 Hardening Middleware Stack 활성화 (Redis 업그레이드)")
        print("   ✅ TraceId: 요청 추적 ID 추가")
        print("   ✅ RequestSizeLimit: 페이로드 크기 제한 (413)")
        print("   ✅ Redis RateLimit: 분산 속도 제한 (429) - slowapi + Redis")
        print("   ✅ SqlGuard: SQL 인젝션 패턴 감지 (400)")
        print("   📊 Redis-backed: distributed 환경 지원 (OWASP 2025 준수)")

    except Exception as e:
        print(f"⚠️ Phase 2 Hardening Middleware 설정 실패: {e}")
        import traceback

        traceback.print_exc()


def _setup_cache_middleware(app: FastAPI) -> None:
    """Setup cache middleware for API responses."""
    try:
        from AFO.api.middleware.cache_middleware import CacheMiddleware

        # Add cache middleware (before other middleware for optimal performance)
        app.add_middleware(CacheMiddleware)
        print("✅ API Cache Middleware 활성화")

    except Exception as e:
        print(f"⚠️ Cache Middleware 설정 실패: {e}")
        import traceback

        traceback.print_exc()


def _setup_performance_middleware(app: FastAPI) -> None:
    """Setup performance monitoring middleware."""
    try:
        from AFO.api.middleware.performance_middleware import PerformanceMiddleware

        # Add performance middleware
        app.add_middleware(PerformanceMiddleware)
        print("✅ Performance Monitoring Middleware 활성화")

    except Exception as e:
        print(f"⚠️ Performance Middleware 설정 실패: {e}")
        import traceback

        traceback.print_exc()


def _setup_monitoring_middleware(app: FastAPI) -> None:
    """Setup monitoring and metrics middleware."""
    try:
        from AFO.api.middleware.prometheus import PrometheusMiddleware

        # Add Prometheus middleware
        app.add_middleware(PrometheusMiddleware, service_name="afo-kingdom-api")
        print("✅ Prometheus Metrics Middleware 활성화")

        # Add metrics endpoint
        from fastapi.routing import APIRouter

        from AFO.api.middleware.prometheus import metrics_endpoint

        metrics_router = APIRouter()
        metrics_router.get("/metrics")(metrics_endpoint)
        app.include_router(metrics_router)

        print("✅ Prometheus Metrics Endpoint 추가 (/metrics)")

    except Exception as e:
        print(f"⚠️ Prometheus Middleware 설정 실패: {e}")
        import traceback

        traceback.print_exc()
