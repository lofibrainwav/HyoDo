# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO API Routers
Phase 2 리팩토링: 라우터 분리
"""

try:
    from AFO.health import router as health_router
except ImportError:
    health_router = None

try:
    from AFO.root import router as root_router
except ImportError:
    root_router = None

__all__ = ["health_router", "root_router"]
