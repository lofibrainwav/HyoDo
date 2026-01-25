from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi import FastAPI

from AFO.api.compat import (
    aicpa_router,
    auth_router,
    budget_router,
    chancellor_router,
    chat_router,
    council_router,
    debugging_router,
    debugging_stream_router,
    decree_router,
    education_system_router,
    evolution_router,
    external_router,
    finance_router,
    got_router,
    grok_stream_router,
    health_router,
    learning_log_router,
    learning_pipeline,
    matrix_router,
    modal_data_router,
    multi_agent_router,
    n8n_router,
    personas_router,
    pillars_router,
    rag_query_router,
    root_router,
    serenity_router,
    skills_router,
    ssot_router,
    streams_router,
    system_health_router,
    tax_router,
    thoughts_router,
    trinity_policy_router,
    trinity_sbt_router,
    users_router,
    voice_router,
    wallet_router,
)

# Optional imports - these may fail if modules are missing
try:
    from AFO.api.routes.rag_stream import router as rag_stream_router
except ImportError:
    rag_stream_router = None

try:
    from api.routes.time_travel import router as time_travel_router
except ImportError:
    time_travel_router = None

try:
    from AFO.api.routers.compat import router as compat_router
except ImportError:
    compat_router = None

try:
    from api.routes.system_health import sse_ssot_router
except ImportError:
    sse_ssot_router = None

try:
    from AFO.api.routes.philosophical_copilot import (
        router as philosophical_copilot_router,
    )
except ImportError:
    philosophical_copilot_router = None

try:
    from AFO.api.routers.rag_query import router as rag_router
except ImportError:
    rag_router = None

try:
    from AFO.api.routes.comprehensive_health import (
        router as comprehensive_health_router,
    )
except ImportError:
    comprehensive_health_router = None

try:
    from AFO.afo_soul_engine.routers.intake import router as intake_router
except ImportError:
    intake_router = None

# GenUI Router (Legacy removed in Phase 31)
gen_ui_router = None

try:
    from AFO.api.routers.family import router as family_router
except ImportError:
    family_router = None

try:
    from AFO.api.routers.cache import router as cache_router
except ImportError:
    cache_router = None

try:
    from api.routers.client_stats import router as client_stats_router
except ImportError:
    client_stats_router = None

try:
    from AFO.api.routers.julie_royal import router as julie_royal_router
except ImportError:
    julie_royal_router = None

try:
    from AFO.api.routes.julie import julie_router
except ImportError:
    julie_router = None

try:
    from AFO.api.routers.kakao_router import router as kakao_router
except ImportError:
    kakao_router = None


try:
    from AFO.api.routers.discord_router import router as discord_router
except ImportError:
    discord_router = None

try:
    from api.routes.gemini_gem import router as gemini_gem_router
except ImportError:
    gemini_gem_router = None


# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Kingdom API Router Registration (아름다운 코드 적용)

Trinity Score 기반 아름다운 코드로 구현된 중앙 집중식 라우터 등록 시스템.
모듈화, 타입 안전성, 문서화를 통해 유지보수성과 확장성을 보장.

Author: AFO Kingdom Development Team
Date: 2025-12-24
Version: 2.0.0 (Beautiful Code Edition)
"""

logger = logging.getLogger(__name__)


def _coerce_tags(tags: Sequence[str] | None) -> list[str] | None:
    """FastAPI tags 타입을 list[str]로 안전하게 변환 (眞)"""
    if tags is None:
        return None
    return list(tags)


class AFORouterManager:
    """
    AFO Kingdom Router Manager (아름다운 코드 적용)

    Trinity Score 기반 라우터 관리를 통해 체계적이고 아름다운 API 구조를 유지.
    각 라우터 그룹을 별도 메서드로 분리하여 단일 책임 원칙 준수.

    Attributes:
        app: FastAPI 애플리케이션 인스턴스
        registered_routers: 등록된 라우터 수 카운터
    """

    def __init__(self, app: FastAPI) -> None:
        """Initialize router manager with FastAPI app.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.registered_routers = 0
        logger.info("AFO Router Manager initialized with beautiful code principles")

    def setup_all_routers(self) -> None:
        """Setup and register all API routers in organized manner.

        Trinity Score: 美 (Beauty) - 체계적이고 아름다운 라우터 구성
        """
        logger.info("Starting router registration process...")

        # Core system routers (highest priority)
        self._register_core_routers()

        # Feature routers (business logic)
        self._register_feature_routers()

        # Phase-specific routers (incremental development)
        self._register_phase_routers()

        # Legacy and compatibility routers (last resort)
        self._register_legacy_routers()

        logger.info(f"Router registration completed. Total: {self.registered_routers} routers")

    def _register_core_routers(self) -> None:
        """Register core system routers (Health, Root, Streams).

        Trinity Score: 眞 (Truth) - 시스템 핵심 기능 우선 등록
        """
        logger.debug("Registering core system routers...")

        # Health and root endpoints
        self._safe_register_router(root_router, tags=["Core"])
        self._safe_register_router(health_router, tags=["Core"])

        # Matrix streams (must be mounted before other routers)
        self._safe_register_router(streams_router, prefix="/api/stream", tags=["Matrix Stream"])
        self._safe_register_router(matrix_router, prefix="/api", tags=["Matrix Stream (Phase 10)"])

    def _register_feature_routers(self) -> None:
        """Register feature-specific routers (Business Logic).

        Trinity Score: 善 (Goodness) - 비즈니스 로직 체계적 구성
        """
        logger.debug("Registering feature routers...")

        # 5 Pillars system
        self._safe_register_router(pillars_router, tags=["5 Pillars"])

        # System health and monitoring
        self._safe_register_router(system_health_router, tags=["System Health"])

        # SSE SSOT Router (canonical /api/logs/stream + aliases)
        try:
            self._safe_register_router(sse_ssot_router, tags=["SSE SSOT"])
        except ImportError:
            logger.warning("SSE SSOT Router not available")

        # Multi-agent and AI systems
        self._safe_register_router(multi_agent_router)
        self._safe_register_router(got_router, prefix="/api/got", tags=["Graph of Thought"])
        self._safe_register_router(n8n_router, prefix="/api/n8n", tags=["N8N Integration"])

        # API and financial systems
        self._safe_register_router(wallet_router, tags=["API Wallet"])
        self._safe_register_router(trinity_policy_router, tags=["trinity"])
        self._safe_register_router(trinity_sbt_router, prefix="/api", tags=["trinity"])
        self._safe_register_router(tax_router, tags=["Tax Engine"])

        # User management systems
        self._safe_register_router(users_router, tags=["肝 시스템 - 사용자 관리"])
        self._safe_register_router(auth_router, tags=["心 시스템 - 인증"])

        # Communication systems
        self._safe_register_router(chat_router, prefix="/api/chat", tags=["Chat"])

        # Education and data systems
        self._safe_register_router(
            education_system_router, prefix="/api/education", tags=["Education System"]
        )
        self._safe_register_router(modal_data_router, prefix="/api/modal", tags=["Modal Data"])

        # Advanced AI systems
        self._safe_register_router(rag_query_router, prefix="/api", tags=["Brain Organ (RAG)"])
        self._safe_register_router(rag_stream_router, prefix="/api", tags=["Brain Organ (RAG)"])
        self._safe_register_router(personas_router, tags=["Phase 2: Family Hub OS"])
        self._safe_register_router(thoughts_router, prefix="/api/thoughts", tags=["Thought Stream"])

    def _register_phase_routers(self) -> None:
        """Register phase-specific routers (Incremental Development).

        Trinity Score: 永 (Eternity) - 단계적 개발 지원으로 장기적 유지보수성 확보
        """
        logger.debug("Registering phase-specific routers...")

        # Phase 12-13: Business Intelligence
        self._safe_register_router(budget_router, tags=["Phase 12"])
        self._safe_register_router(aicpa_router, prefix="/api", tags=["AICPA Agent Army"])

        # Phase 16-18: Autonomous Learning
        self._safe_register_router(learning_log_router, tags=["Phase 16"])
        self._safe_register_router(grok_stream_router, tags=["Phase 18"])

        # Phase 23-27: Advanced AI
        self._safe_register_router(voice_router, prefix="/api", tags=["Voice Interface"])
        self._safe_register_router(council_router, prefix="/api", tags=["Council of Minds"])
        self._safe_register_router(learning_pipeline, prefix="/api", tags=["AI Self-Improvement"])
        self._safe_register_router(evolution_router, tags=["Evolution (DGM)"])

        # Phase 29: Automated Debugging System
        self._safe_register_router(debugging_router, tags=["Automated Debugging"])
        self._safe_register_router(debugging_stream_router, tags=["Automated Debugging"])

        self._safe_register_router(decree_router, tags=["Royal Decrees (Phase 12)"])
        self._safe_register_router(external_router, tags=["Phase 13: External Interface"])
        self._safe_register_router(serenity_router, prefix="/api", tags=["Serenity (GenUI)"])

        # Philosophical Copilot (眞善美孝永 철학 실시간 모니터링)
        try:
            self._safe_register_router(philosophical_copilot_router, tags=["철학적 Copilot"])
        except ImportError:
            logger.warning("Philosophical Copilot Router not available")

        # Chancellor and streaming systems
        self._safe_register_router(chancellor_router, tags=["LangGraph Optimized"])

        # Time Travel Router (TICKET-078 - 북극성)
        if time_travel_router:
            self._safe_register_router(time_travel_router, tags=["Time Travel"])
        else:
            logger.warning("Time Travel Router not available")

        # RAG Streaming for T2.1
        try:
            self._safe_register_router(rag_router, prefix="/api", tags=["RAG Streaming"])
        except ImportError:
            logger.warning("RAG Router not available")

        # RAG Stream Router (TICKET-079 - 스트리밍 중 interrupt → fork → resume)
        try:
            self._safe_register_router(rag_stream_router, tags=["RAG Streaming"])
        except ImportError:
            logger.warning("RAG Stream Router not available")

        # NOTE: system_stream router is deprecated. SSE is now consolidated in sse_ssot_router (system_health.py)
        # Keeping import as fallback but not registering to prevent route conflicts.
        # try:
        #     from AFO.api.routes.system_stream import router as system_stream_router
        #     self._safe_register_router(system_stream_router, tags=["SSE 스트리밍"])
        # except ImportError:
        #     logger.warning("System Stream Router not available")

        # Additional systems
        self._safe_register_router(finance_router)
        self._safe_register_router(ssot_router)

        # Discord Bot Bridge (Meta-Intelligence)
        self._safe_register_router(discord_router, tags=["Discord Bot Bridge"])

        # KakaoBot Bridge (Meta-Intelligence)
        self._safe_register_router(kakao_router, tags=["KakaoBot Bridge"])

        # Gemini Gem Chat Widget
        self._safe_register_router(gemini_gem_router, tags=["Gemini Gem"])

    def _register_legacy_routers(self) -> None:
        """Register legacy and compatibility routers.

        Trinity Score: 孝 (Serenity) - 레거시 호환성으로 마찰 최소화
        """
        logger.debug("Registering legacy routers...")

        # Skills API (Critical for functionality)
        self._register_skills_router()

        # Comprehensive health and monitoring
        self._register_comprehensive_health()

        # Management APIs
        self._register_management_apis()

        # Compatibility routers
        self._register_compatibility_routers()

    def _register_skills_router(self) -> None:
        """Register Skills API router with enhanced error handling."""
        if not skills_router:
            logger.warning("Skills router not available")
            return

        try:
            routes_before = len([r for r in self.app.routes if hasattr(r, "path")])
            prefix = "/api/skills"
            router_prefix = getattr(skills_router, "prefix", "")
            if router_prefix:
                self.app.include_router(skills_router, tags=["Skills"])
            else:
                self.app.include_router(skills_router, prefix=prefix, tags=["Skills"])
            routes_after = len([r for r in self.app.routes if hasattr(r, "path")])
            self.registered_routers += routes_after - routes_before
            logger.info(
                f"Skills API registered successfully ({routes_after - routes_before} routes)"
            )
        except Exception as e:
            logger.error("Skills router registration failed: %s", e)

    def _register_comprehensive_health(self) -> None:
        """Register comprehensive health check router."""
        try:
            self._safe_register_router(comprehensive_health_router, tags=["Health"])
        except ImportError:
            logger.warning("Comprehensive Health Check Router not available")

    def _register_management_apis(self) -> None:
        """Register management and utility APIs."""
        # MCP Tools, Integrity Check, Git Status, Context7, A2A
        management_routers = [
            ("AFO.api.routes.mcp_tools", "MCP Tools"),
            ("AFO.api.routes.integrity_check", "Integrity Check"),
            ("AFO.api.routes.git_status", "Git Status"),
            ("AFO.api.routes.context7", "Context7 Knowledge Base"),
            ("api.routes.a2a_agent_card", "A2A Protocol"),
        ]

        for module_path, name in management_routers:
            try:
                module = __import__(module_path, fromlist=["router"])
                router = module.router
                self._safe_register_router(router, tags=[name])
            except (ImportError, AttributeError) as e:
                logger.warning("%s router not available: %s", name, e)

    def _register_compatibility_routers(self) -> None:
        """Register compatibility and legacy routers."""
        # Intake API
        try:
            self._safe_register_router(intake_router, prefix="/api/intake", tags=["Intake"])
        except ImportError:
            logger.warning("Intake API router not available")

        # GenUI Engine
        try:
            self._safe_register_router(gen_ui_router, tags=["GenUI"])
        except ImportError as e:
            logger.error("GenUI Engine not available: %s", e, exc_info=True)
            # logger.warning("GenUI Engine not available")

        # Family Hub
        try:
            self._safe_register_router(family_router, tags=["Family Hub"])
            self._safe_register_router(family_router, prefix="/api", tags=["Family Hub"])
        except ImportError:
            logger.warning("Family Hub router not available")

        # Cache Metrics
        try:
            self._safe_register_router(cache_router, tags=["Cache Metrics"])
        except ImportError:
            logger.warning("Cache Metrics router not available")

        # Client Stats (Data Driven - Eliminating Hardcoding)
        try:
            self._safe_register_router(client_stats_router, tags=["Client Stats"])
        except ImportError:
            logger.warning("Client Stats router not available")

        # Julie Royal
        try:
            self._safe_register_router(julie_royal_router, tags=["Julie Royal"])
        except ImportError:
            logger.warning("Julie Royal router not available")

        # Strangler Fig Compatibility
        if compat_router:
            self._safe_register_router(compat_router, prefix="/api", tags=["Strangler Fig"])

    def _safe_register_router(
        self, router: Any | None, prefix: str = "", tags: list[str] | None = None
    ) -> None:
        """Safely register a router with error handling.

        Args:
            router: Router object to register
            prefix: URL prefix for the router
            tags: Tags for API documentation
        """
        if not router:
            return

        try:
            routes_before = len([r for r in self.app.routes if hasattr(r, "path")])
            if prefix and tags:
                self.app.include_router(router, prefix=prefix, tags=cast("Any", tags))
            elif prefix:
                self.app.include_router(router, prefix=prefix)
            elif tags:
                self.app.include_router(router, tags=cast("Any", tags))
            else:
                self.app.include_router(router)

            routes_after = len([r for r in self.app.routes if hasattr(r, "path")])
            self.registered_routers += routes_after - routes_before

        except Exception as e:
            logger.error("Router registration failed: %s", e)


# Global function for backward compatibility
def setup_routers(app: FastAPI) -> None:
    """Setup all routers using the beautiful RouterManager.

    Args:
        app: FastAPI application instance
    """
    manager = AFORouterManager(app)
    manager.setup_all_routers()
