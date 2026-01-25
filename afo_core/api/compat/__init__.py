"""API Compatibility Package

모듈화된 compat 패키지.
眞善美孝永 원칙에 따라 안전한 import와 설정 관리를 제공합니다.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = object  # type: ignore[assignment, misc]

from .facade import HTMLDataFacade
from .metrics import TrinityMetrics
from .models import HTMLSectionData
from .providers import PhilosophyDataProvider, PortDataProvider

# ═══════════════════════════════════════════════════════════════════════════════
# Trinity Score 계산 (眞: Truth - 정확한 계산)
# ═══════════════════════════════════════════════════════════════════════════════


def calculate_trinity(scores: dict[str, float]) -> float:
    """Trinity Score 계산 함수

    Args:
        scores: 각 기둥별 점수 (0-100)

    Returns:
        계산된 Trinity Score (0-100)
    """
    weights = {
        "truth": 0.35,
        "goodness": 0.35,
        "beauty": 0.20,
        "serenity": 0.08,
        "eternity": 0.02,
    }

    normalized = {k: v / 100.0 for k, v in scores.items()}
    return sum(normalized.get(k, 0) * weights[k] for k in weights) * 100


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience Functions (테스트 호환성)
# ═══════════════════════════════════════════════════════════════════════════════

# 싱글톤 facade 인스턴스
_facade = HTMLDataFacade()
html_facade = _facade  # 호환성을 위한 alias


def get_philosophy_pillars() -> dict[str, Any]:
    """철학 기둥 데이터 조회"""
    return _facade.get_philosophy_data()


def get_service_ports() -> list[dict[str, str]]:
    """서비스 포트 데이터 조회"""
    return _facade.get_port_data()


def get_personas_list() -> list[dict[str, str]]:
    """페르소나 목록 조회"""
    return _facade.get_persona_data()


def get_royal_constitution() -> list[dict[str, str]]:
    """왕국 규칙 조회"""
    return _facade.get_royal_rules_data()


def get_system_architecture() -> dict[str, Any]:
    """시스템 아키텍처 조회"""
    return _facade.get_architecture_data()


def get_project_stats() -> dict[str, int]:
    """프로젝트 통계 조회"""
    return _facade.get_stats_data()


# ═══════════════════════════════════════════════════════════════════════════════
# Chancellor API Models (眞: Truth 타입 안전성)
# ═══════════════════════════════════════════════════════════════════════════════


class ChancellorInvokeRequest(BaseModel):
    """Chancellor 호출 요청 모델 - Phase 11 확장 (Strangler Fig)"""

    input: str
    engine: str | None = None
    mode: str | None = None
    options: dict[str, str] | None = None

    # Phase 11 확장: chancellor_router.py 요구사항 추가
    query: str | None = None  # Backward compatibility
    timeout_seconds: int = 30
    provider: str = "auto"
    ollama_model: str | None = None
    ollama_timeout_seconds: int | None = None
    ollama_num_ctx: int | None = None
    ollama_num_thread: int | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    thread_id: str | None = None
    fallback_on_timeout: bool = True
    auto_run: bool = True
    max_strategists: int = 3


class ChancellorInvokeResponse(BaseModel):
    """Chancellor 호출 응답 모델"""

    result: str
    engine_used: str
    execution_time: float
    mode: str
    metadata: dict[str, str] | None = None
    analysis_results: dict[str, Any] | None = None  # PH30 Expansion: 노드 분석 결과 포함


# AntiGravity control function (compat)
def get_antigravity_control() -> Any:
    """AntiGravity 제어 객체를 반환한다.

    우선순위:
    1) `AFO.config.antigravity.antigravity` (정식)
    2) 최소 기능을 가진 fallback (AUTO_DEPLOY/DRY_RUN_DEFAULT 등)
    """
    try:
        from AFO.config.antigravity import antigravity

        return antigravity
    except Exception:
        return SimpleNamespace(
            ENVIRONMENT=os.getenv("ENVIRONMENT", "dev"),
            AUTO_DEPLOY=os.getenv("AUTO_DEPLOY", "true").lower() == "true",
            DRY_RUN_DEFAULT=os.getenv("DRY_RUN_DEFAULT", "true").lower() == "true",
            AUTO_SYNC=os.getenv("AUTO_SYNC", "true").lower() == "true",
        )


# ANTHROPIC_AVAILABLE definition for compatibility (Truth)
ANTHROPIC_AVAILABLE = os.getenv("ANTHROPIC_API_KEY") is not None
OPENAI_AVAILABLE = os.getenv("OPENAI_API_KEY") is not None


# Safe settings import (孝: Serenity - graceful fallback)
def get_settings_safe() -> None:
    """안전한 설정 조회 함수 (fallback 지원)"""
    try:
        from AFO.config.settings import settings

        return settings
    except ImportError:
        return None


# Safe router imports (孝: Serenity - graceful fallback)
def _safe_import_routers() -> None:
    """라우터들을 안전하게 import (실패 시 빈 dict 반환)"""
    routers = {}

    # 각 라우터를 안전하게 import (module_path, router_attr)
    router_imports = [
        # AFO.api.routers.*
        ("aicpa_router", "AFO.api.routers.aicpa", "router"),
        ("auth_router", "AFO.api.routers.auth", "router"),
        ("budget_router", "AFO.api.routers.budget", "router"),
        ("council_router", "AFO.api.routers.council", "router"),
        ("debugging_router", "AFO.api.routers.debugging", "router"),
        ("decree_router", "AFO.api.routers.decree_router", "router"),
        ("evolution_router", "AFO.api.routers.evolution_router", "router"),
        ("external_router", "AFO.api.routers.external_router", "router"),
        ("finance_router", "AFO.api.routers.finance", "router"),
        ("got_router", "AFO.api.routers.got", "router"),
        ("grok_stream_router", "AFO.api.routers.grok_stream", "router"),
        ("health_router", "AFO.api.routers.health", "router"),
        ("learning_log_router", "AFO.api.routers.learning_log_router", "router"),
        ("learning_pipeline", "AFO.api.routers.learning_pipeline", "router"),
        ("matrix_router", "AFO.api.routers.matrix", "router"),
        ("modal_data_router", "AFO.api.routers.modal_data", "router"),
        ("multi_agent_router", "AFO.api.routers.multi_agent", "router"),
        ("n8n_router", "AFO.api.routers.n8n", "router"),
        ("personas_router", "AFO.api.routers.personas", "router"),
        ("rag_query_router", "AFO.api.routers.rag_query", "router"),
        ("root_router", "AFO.api.routers.root", "router"),
        ("skills_router", "AFO.api.routers.skills", "router"),
        ("ssot_router", "AFO.api.routers.ssot", "router"),
        ("users_router", "AFO.api.routers.users", "router"),
        ("voice_router", "AFO.api.routers.voice", "router"),
        # AFO.api.routes.*
        ("chat_router", "AFO.api.routes.chat", "router"),
        ("debugging_stream_router", "AFO.api.routes.debugging_stream", "router"),
        ("education_system_router", "AFO.api.routers.thoughts", "router"),
        ("pillars_router", "AFO.api.routes.pillars", "router"),
        ("serenity_router", "AFO.api.routes.serenity_router", "router"),
        ("streams_router", "AFO.api.routes.streams", "router"),
        ("system_health_router", "AFO.api.routes.system_health", "router"),
        ("tax_router", "AFO.api.routes.tax", "router"),
        ("thoughts_router", "AFO.api.routers.thoughts", "router"),
        ("trinity_policy_router", "AFO.api.routes.trinity_policy", "router"),
        ("trinity_sbt_router", "AFO.api.routes.trinity_sbt", "router"),
        ("wallet_router", "AFO.api.routes.wallet", "wallet_router"),
    ]

    for router_name, module_path, router_attr in router_imports:
        try:
            module = __import__(module_path, fromlist=[router_attr])
            routers[router_name] = getattr(module, router_attr, None)
        except (ImportError, AttributeError):
            # Import 실패 시 None으로 설정 (孝: Serenity)
            routers[router_name] = None

    return routers


# Chancellor router needs special handling
def _get_chancellor_router() -> None:
    """Chancellor router 특별 처리"""
    try:
        from AFO.api.routers.chancellor_router import router

        return router
    except ImportError:
        try:
            from api.routers.chancellor_router import router

            return router
        except ImportError:
            return None


# 라우터들 동적 import
_routers = _safe_import_routers()

# 각 라우터를 전역 변수로 설정
aicpa_router = _routers.get("aicpa_router")
auth_router = _routers.get("auth_router")
budget_router = _routers.get("budget_router")
chancellor_router = _get_chancellor_router()
chat_router = _routers.get("chat_router")
council_router = _routers.get("council_router")
debugging_router = _routers.get("debugging_router")
debugging_stream_router = _routers.get("debugging_stream_router")
decree_router = _routers.get("decree_router")
education_system_router = _routers.get("education_system_router")
evolution_router = _routers.get("evolution_router")
external_router = _routers.get("external_router")
finance_router = _routers.get("finance_router")
got_router = _routers.get("got_router")
grok_stream_router = _routers.get("grok_stream_router")
health_router = _routers.get("health_router")
learning_log_router = _routers.get("learning_log_router")
learning_pipeline = _routers.get("learning_pipeline")
matrix_router = _routers.get("matrix_router")
modal_data_router = _routers.get("modal_data_router")
multi_agent_router = _routers.get("multi_agent_router")
n8n_router = _routers.get("n8n_router")
personas_router = _routers.get("personas_router")
pillars_router = _routers.get("pillars_router")
rag_query_router = _routers.get("rag_query_router")
root_router = _routers.get("root_router")
serenity_router = _routers.get("serenity_router")
skills_router = _routers.get("skills_router")
ssot_router = _routers.get("ssot_router")
streams_router = _routers.get("streams_router")
system_health_router = _routers.get("system_health_router")
tax_router = _routers.get("tax_router")
thoughts_router = _routers.get("thoughts_router")
trinity_policy_router = _routers.get("trinity_policy_router")
trinity_sbt_router = _routers.get("trinity_sbt_router")
users_router = _routers.get("users_router")
voice_router = _routers.get("voice_router")
wallet_router = _routers.get("wallet_router")

__all__ = [
    # Models & Facades
    "HTMLSectionData",
    "HTMLDataFacade",
    "html_facade",
    "PhilosophyDataProvider",
    "PortDataProvider",
    "TrinityMetrics",
    # Chancellor API Models
    "ChancellorInvokeRequest",
    "ChancellorInvokeResponse",
    # Settings & Utilities
    "get_settings_safe",
    "get_antigravity_control",
    "ANTHROPIC_AVAILABLE",
    # Trinity & Convenience Functions
    "calculate_trinity",
    "get_philosophy_pillars",
    "get_service_ports",
    "get_personas_list",
    "get_royal_constitution",
    "get_system_architecture",
    "get_project_stats",
    # Routers (safe imports)
    "aicpa_router",
    "auth_router",
    "budget_router",
    "chancellor_router",
    "chat_router",
    "council_router",
    "debugging_router",
    "debugging_stream_router",
    "decree_router",
    "education_system_router",
    "evolution_router",
    "external_router",
    "finance_router",
    "got_router",
    "grok_stream_router",
    "health_router",
    "learning_log_router",
    "learning_pipeline",
    "matrix_router",
    "modal_data_router",
    "multi_agent_router",
    "n8n_router",
    "personas_router",
    "pillars_router",
    "rag_query_router",
    "root_router",
    "serenity_router",
    "skills_router",
    "ssot_router",
    "streams_router",
    "system_health_router",
    "tax_router",
    "thoughts_router",
    "trinity_policy_router",
    "trinity_sbt_router",
    "users_router",
    "voice_router",
    "wallet_router",
]
