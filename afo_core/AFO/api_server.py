from __future__ import annotations

import sys

# Python 버전 검증 (眞: Truth - 3.12 전용 고정)
if sys.version_info < (3, 12):  # noqa: UP036 - 의도적인 런타임 버전 체크
    print(f"❌ 에러: Python 3.12 이상이 필요합니다. 현재 버전: {sys.version}")
    sys.exit(1)

print("LOADING LOCAL API SERVER")

import asyncio
import json
import logging
import os  # Added for env check
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

# Add trinity-os to python path for Context7 dependency
current_dir = Path(__file__).resolve().parent  # AFO/
package_root = current_dir.parent  # packages/afo-core/
monorepo_root = package_root.parent  # packages/
trinity_os_path = monorepo_root / "trinity-os"
if str(trinity_os_path) not in sys.path:
    sys.path.insert(0, str(trinity_os_path))

import uvicorn
from fastapi import FastAPI, Header, HTTPException  # Added for security
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
from starlette.responses import Response

from AFO.api.config import get_app_config, get_server_config
from AFO.api.middleware import setup_middleware
from AFO.api.observability import instrument_fastapi, setup_opentelemetry, setup_sentry
from AFO.api.patches import patch_typing_inspection_if_needed
from AFO.api.router_manager import setup_routers
from AFO.services.debugging_agent import HealingAgent

# Apply typing inspection patch
patch_typing_inspection_if_needed()

# Router imports
from AFO.api.routers.chancellor_router import router as chancellor_router
from AFO.api.routers.gen_ui_new import router as gen_ui_router

# Optional router imports
try:
    from AFO.api.routers.multimodal import router as multimodal_router
except ImportError:
    multimodal_router = None

try:
    from api.routers.ai_diagram import router as ai_diagram_router
except ImportError:
    ai_diagram_router = None

try:
    from api.routers.collaboration import router as collaboration_router
except ImportError:
    collaboration_router = None

try:
    from AFO.api.routers.kakao_router import router as kakao_router
except ImportError:
    kakao_router = None

try:
    from AFO.api.routers.discord_router import router as discord_router
except ImportError:
    discord_router = None

try:
    from afo_soul_engine.routers.onboarding import router as onboarding_router
except ImportError:
    onboarding_router = None

import datetime

# Optional Auth & Middleware Imports
try:
    from AFO.api.auth.api_key_acl import DEFAULT_ENDPOINT_SCOPES, acl
except (ImportError, ModuleNotFoundError):
    DEFAULT_ENDPOINT_SCOPES = {}
    acl = None

try:
    from AFO.api.middleware.authz import APIKeyAuthMiddleware
except ImportError:
    APIKeyAuthMiddleware = None

try:
    from AFO.api.middleware.metrics import MetricsMiddleware
except ImportError:
    MetricsMiddleware = None

try:
    from AFO.api.routers.rag_query import router as rag_router
except ImportError:
    rag_router = None

try:
    from AFO.api.routers.auth import router as auth_router
except ImportError:
    auth_router = None

try:
    from AFO.api.routes.trinity import router as trinity_router
except ImportError:
    trinity_router = None

from AFO.domain.metrics.trinity_manager import trinity_manager

try:
    from AFO.api.routes.mygpt.contexts import router as mygpt_contexts_router
except ImportError:
    mygpt_contexts_router = None

try:
    from AFO.api.routes.mygpt.transfer import router as mygpt_transfer_router
except ImportError:
    mygpt_transfer_router = None


try:
    from api.routers.intake import router as intake_router
except ImportError:
    intake_router = None

try:
    from AFO.api.routes.gateway import gateway_router
except ImportError:
    gateway_router = None

# Phase 86: 실제 LLM 연동 - LLM 라우터 등록
try:
    from AFO.api.routes.llm import llm_router
except ImportError:
    llm_router = None

try:
    from AFO.api.routes.probe import router as probe_router
except ImportError:
    probe_router = None

try:
    from packages.afo_core.api.routers.core_analysis import router as core_analysis_router
except ImportError:
    # Try alternate path if first one fails
    try:
        from api.routers import core_analysis, family, trinity_debate
        from application.agents.orchestrator import agent_orchestrator  # noqa: F401

        core_analysis_router = core_analysis.router
        family_router = family.router
        trinity_debate_router = trinity_debate.router
    except ImportError:
        core_analysis_router = None
        family_router = None
        trinity_debate_router = None

# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom API Server (아름다운 코드 적용)
FastAPI 기반 AFO 왕국 Soul Engine API 서버

이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다.
Trinity Score 기반 품질 관리 및 아름다운 코드 원칙 준수.
Debugging Super Agent (2026 Vision) Integrated (眞·永)
"""

# 2026 Debugging Super Agent
ExceptionHandler = Callable[[Request, Exception], Response | Awaitable[Response]]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AFOServer:
    """AFO Kingdom API Server Manager

    아름다운 코드 원칙을 준수하는 API 서버 관리 클래스.
    Trinity Score 기반 품질 관리를 통해 안정성과 확장성을 보장.
    """

    def __init__(self) -> None:
        """Initialize AFO API Server with beautiful code principles."""
        self._setup_python_path()
        setup_sentry()
        setup_opentelemetry()
        self.app = self._create_app()
        self.limiter = self._create_limiter()
        self.healing_agent = HealingAgent()  # Initialize Super Agent
        self._background_tasks: set[asyncio.Task[Any]] = set()  # Prevent GC of async tasks
        self._configure_app()
        self._setup_components()

        logger.info("AFO Kingdom API Server initialized with beautiful code principles")

    def _setup_python_path(self) -> None:
        """Setup Python path for AFO imports."""
        afo_root = str(Path(__file__).resolve().parent.parent)
        if afo_root not in sys.path:
            sys.path.insert(0, afo_root)
            logger.debug(f"Added AFO root to Python path: {afo_root}")

    def _create_app(self) -> FastAPI:
        """Create FastAPI application instance."""
        try:
            app = get_app_config()
            logger.info("FastAPI application created")

            # Register all routers
            self._register_routers(app)
            return app
        except Exception as e:
            logger.error(f"Failed to create app: {e}")
            raise

    def _register_routers(self, app: FastAPI) -> None:
        """Register all API routers."""
        routers = [
            (gen_ui_router, None, None, "GenUI Router (New)"),
            (chancellor_router, None, None, "Chancellor Router"),
            (multimodal_router, None, None, "Multimodal Router"),
            (rag_router, "/api", None, "RAG Router"),
            (auth_router, None, None, "Auth Router"),
            (trinity_router, None, ["Trinity"], "Trinity Router (Updated with TrinityManager)"),
            (mygpt_contexts_router, None, ["MyGPT"], "MyGPT Contexts Router"),
            (mygpt_transfer_router, None, ["MyGPT"], "MyGPT Transfer Router"),
            (llm_router, None, ["LLM"], "LLM Integration Router (Phase 86)"),
            (gateway_router, None, ["Julie-Gateway"], "Julie CPA Gateway Router (Phase 4)"),
            (intake_router, "/api/intake", ["Intake"], "Intake Router"),
            (ai_diagram_router, None, None, "AI Diagram Router"),
            (collaboration_router, None, None, "Collaboration Router"),
            (discord_router, None, None, "Discord Bot Router"),
            (kakao_router, None, None, "KakaoBot Router"),
            (onboarding_router, None, None, "Onboarding Router"),
            (core_analysis_router, None, None, "AI Core Analysis Router (Phase 5)"),
            (probe_router, "/api/v1/probe", ["Verification"], "Microscopic Internal Probe"),
        ]

        for router, prefix, tags, name in routers:
            if router is None:
                continue
            try:
                if prefix and tags:
                    app.include_router(router, prefix=prefix, tags=tags)
                elif prefix:
                    app.include_router(router, prefix=prefix)
                else:
                    app.include_router(router)
                logger.info(f"{name} registered successfully")
            except Exception as e:
                logger.warning(f"{name} registration failed: {e}")

        # Phase 5: Real Agent Intelligence
        try:
            app.include_router(core_analysis.router)
            logger.info("AI Core Analysis Router (Phase 5) registered successfully")
        except NameError:
            logger.warning("AI Core Analysis Router (Phase 5) not available")
        except Exception as e:
            logger.warning(f"AI Core Analysis Router (Phase 5) registration failed: {e}")

        # Phase 5.5: Family Hub
        try:
            app.include_router(family.router)
            logger.info("Family Hub Router (Phase 5.5) registered successfully")
        except NameError:
            logger.warning("Family Hub Router (Phase 5.5) not available")
        except Exception as e:
            logger.warning(f"Family Hub Router (Phase 5.5) registration failed: {e}")

        # Phase 6: Trinity Resonance
        try:
            app.include_router(trinity_debate.router)
            logger.info("Trinity Debate Router (Phase 6) registered successfully")
        except NameError:
            logger.warning("Trinity Debate Router (Phase 6) not available")
        except Exception as e:
            logger.warning(f"Trinity Debate Router (Phase 6) registration failed: {e}")

    def _create_limiter(self) -> Limiter:
        """Create rate limiter for API protection."""
        from AFO.core.limiter import limiter

        logger.info("Shared Rate limiter configured")
        return limiter

    def _configure_app(self) -> None:
        """Configure FastAPI application with middleware and handlers."""
        # Configure rate limiting
        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(
            RateLimitExceeded, cast("ExceptionHandler", _rate_limit_exceeded_handler)
        )

        # Metrics 미들웨어 추가
        if MetricsMiddleware:
            try:
                self.app.add_middleware(MetricsMiddleware)
            except ImportError:
                logger.warning("⚠️ MetricsMiddleware not available")

        # ACL 미들웨어 추가
        if APIKeyAuthMiddleware:
            try:
                self.app.add_middleware(APIKeyAuthMiddleware)
            except Exception as e:
                logger.warning(f"⚠️ Failed to add APIKeyAuthMiddleware: {e}")
        else:
            logger.warning("⚠️ APIKeyAuthMiddleware not available")

        # ACL 초기화
        if acl:
            try:
                for path, method, scopes in DEFAULT_ENDPOINT_SCOPES:
                    acl.add_endpoint_scope(path, method, scopes)
            except Exception as e:
                logger.warning(f"⚠️ API Key ACL setup failed: {e}")
        else:
            logger.warning("⚠️ API Key ACL not available")

        self._setup_event_handlers()
        self._setup_endpoints()

        logger.info("Application configured with security measures")

    def _setup_event_handlers(self) -> None:
        """Setup startup and shutdown event handlers."""

        @self.app.on_event("startup")
        async def start_background_services() -> None:
            """Start background services."""
            if os.getenv("AFO_DEBUG_AGENT_ENABLED") == "1":
                logger.info("🤖 Starting Debugging Super Agent (2026 Vision)...")
                task = asyncio.create_task(self.healing_agent.start())
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            else:
                logger.info("🛡️ Debugging Super Agent is DISABLED (Default Safe Mode).")

        @self.app.on_event("shutdown")
        async def persist_acl_keys() -> None:
            """서버 종료 시 ACL 키 영속 저장"""
            if acl:
                try:
                    acl.persist_all_keys()
                    logger.info("✅ ACL keys persisted on shutdown")
                except Exception as e:
                    logger.warning(f"⚠️  ACL persistence failed on shutdown: {e}")

    def _setup_endpoints(self) -> None:
        """Setup additional API endpoints."""

        @self.app.post("/api/debug/agent/simulate", tags=["Debugging Agent"])
        async def trigger_simulation(
            error_code: str = "DTZ005",
            x_afo_debug_secret: str | None = Header(None, alias="X-AFO-DEBUG-SECRET"),
        ) -> dict[str, Any]:
            """Trigger a self-healing simulation scenario (Protected)."""
            if os.getenv("AFO_DEBUG_AGENT_ENABLED") != "1":
                raise HTTPException(status_code=403, detail="Debugging Agent is disabled.")

            required_secret = os.getenv("AFO_DEBUG_SECRET", "default-dev-secret")
            if x_afo_debug_secret != required_secret:
                raise HTTPException(status_code=401, detail="Invalid Debug Secret.")

            await self.healing_agent.trigger_anomaly(error_code)
            return {
                "message": f"Anomaly {error_code} injected.",
                "agent_name": self.healing_agent.name,
                "current_entropy": self.healing_agent.state.entropy,
            }

        @self.app.get("/metrics")
        async def metrics() -> Response:
            try:
                return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
            except Exception as e:
                logger.error(f"Metrics generation failed: {e}")
                return Response("Internal Server Error", status_code=500)

        @self.app.get("/api/logs/stream", tags=["Logs"])
        async def logs_stream(request: Request):
            """Stream real-time chancellor thoughts via Server-Sent Events."""

            async def event_generator():
                yield {
                    "event": "connected",
                    "data": json.dumps(
                        {
                            "message": "🏰 Chancellor Stream Connected",
                            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                        }
                    ),
                }

                counter = 0
                while True:
                    if await request.is_disconnected():
                        break

                    await asyncio.sleep(15)
                    counter += 1
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps(
                            {
                                "message": f"💓 Chancellor Heartbeat #{counter}",
                                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                            }
                        ),
                    }

            return EventSourceResponse(event_generator())

        @self.app.get("/api/trinity/stream", tags=["Trinity"])
        async def trinity_stream(request: Request):
            """Stream real-time Trinity Score updates via SSE."""

            async def trinity_generator():
                yield {
                    "event": "connected",
                    "data": json.dumps(
                        {
                            "message": "✨ Trinity Score HUD Connected",
                            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                        }
                    ),
                }

                while True:
                    if await request.is_disconnected():
                        break

                    # 眞 (Truth): 실사 구시된 TrinityManager 데이터 연동
                    metrics = trinity_manager.get_current_metrics()
                    metrics_100 = metrics.to_100_scale()

                    pillar_scores = {
                        "truth": metrics_100.truth,
                        "goodness": metrics_100.goodness,
                        "beauty": metrics_100.beauty,
                        "filial_piety": metrics_100.filial_serenity,
                        "eternity": metrics_100.eternity,
                    }

                    yield {
                        "event": "update",
                        "data": json.dumps(
                            {
                                "scores": pillar_scores,
                                "total": round(metrics_100.trinity_score, 2),
                                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                                "note": "Real-time TrinityManager Sync (眞)",
                            }
                        ),
                    }
                    await asyncio.sleep(5)  # 5초마다 업데이트

            return EventSourceResponse(trinity_generator())

    def _setup_components(self) -> None:
        """Setup middleware and routers."""
        try:
            setup_middleware(self.app)
            logger.info("Middleware setup completed")

            setup_routers(self.app)
            logger.info("Router setup completed")

            instrument_fastapi(self.app)

        except Exception:
            logger.exception("Component setup failed")
            raise

    def run_server(self, host: str = "127.0.0.1", port: int = 8010) -> None:
        """Run the API server."""
        logger.info(f"🚀 Starting AFO Kingdom API Server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Global server instance (Singleton pattern for beautiful code)
server = AFOServer()
app = server.app


# Main execution block with proper error handling
if __name__ == "__main__":
    try:
        host, port = get_server_config()
        server.run_server(host=host, port=port)
    except Exception:
        logger.exception("Failed to start server")
        sys.exit(1)
