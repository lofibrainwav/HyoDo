"""
Chancellor Router - Import 및 Fallback 로직
공통 의존성 및 초기화 로직 분리
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Core Imports
# ═══════════════════════════════════════════════════════════════════════════════

from AFO.afo_agent_fabric import _get_cached_engine_status
from AFO.api.chancellor_v2.graph.nodes.execute_node import execute_node
from AFO.api.chancellor_v2.graph.nodes.verify_node import verify_node
from AFO.api.chancellor_v2.graph.runner import run_v2
from AFO.api.chancellor_v2.graph.state import GraphState
from AFO.api.compat import (
    ChancellorInvokeRequest,
    ChancellorInvokeResponse,
    get_antigravity_control,
)
from AFO.api.routes.system_health import get_system_metrics
from AFO.chancellor_graph import (
    ChancellorGraph,
    mipro_node,
)
from AFO.chancellor_graph import (
    build_chancellor_graph as _bcg,
)
from AFO.chancellor_graph import (
    chancellor_graph as _cg,
)
from AFO.config.antigravity import antigravity
from AFO.learning_loader import get_learning_profile
from AFO.llm_router import llm_router as _afol_router
from AFO.rag_flag import execute_rag_with_mode, get_rag_config, init_rag_semaphore
from AFO.rag_shadow import execute_rag_shadow, get_shadow_metrics, is_rag_shadow_enabled
from AFO.trinity_config import BASE_CONFIG, apply_learning_profile
from config.antigravity import antigravity as ag
from llm_router import llm_router as _router

# ═══════════════════════════════════════════════════════════════════════════════
# Antigravity Fallback
# ═══════════════════════════════════════════════════════════════════════════════


class MockAntigravity:
    """Fallback antigravity when real module unavailable."""

    AUTO_DEPLOY = True
    DRY_RUN_DEFAULT = True
    ENVIRONMENT = "dev"


def get_antigravity() -> Any:
    """Get antigravity instance with fallback."""
    try:
        return antigravity
    except Exception:
        try:
            return ag
        except Exception:
            return MockAntigravity()


# ═══════════════════════════════════════════════════════════════════════════════
# Learning Profile Loader
# ═══════════════════════════════════════════════════════════════════════════════

_learning_loader_available = False

try:
    _learning_loader_available = True
    logger.info("✅ Learning profile loader imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Learning profile loader import failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# RAG Shadow Mode (TICKET-008 Phase 1)
# ═══════════════════════════════════════════════════════════════════════════════

_rag_shadow_available = False

try:
    _rag_shadow_available = True
    logger.info("✅ RAG shadow mode imported successfully")
except ImportError:
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../afo"))
        _rag_shadow_available = True
        logger.info("✅ RAG shadow mode imported successfully (relative path)")
    except ImportError as e:
        logger.warning(f"⚠️ RAG shadow mode import failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# RAG Flag + Gradual Mode (TICKET-008 Phase 2 + 3)
# ═══════════════════════════════════════════════════════════════════════════════

_rag_flag_available = False

try:
    init_rag_semaphore()
    _rag_flag_available = True
    logger.info("✅ RAG flag + gradual mode imported successfully")
except ImportError:
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../afo"))
        init_rag_semaphore()
        _rag_flag_available = True
        logger.info("✅ RAG flag + gradual mode imported successfully (relative path)")
    except ImportError as e:
        logger.warning(f"⚠️ RAG flag + gradual mode import failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Chancellor Graph V2
# ═══════════════════════════════════════════════════════════════════════════════

_v2_runner_available = False
_chancellor_import_error: str | None = None

try:
    _v2_runner_available = True
    logger.info("✅ Chancellor V2 runner loaded successfully")
except ImportError as e:
    _chancellor_import_error = str(e)
    logger.warning(f"⚠️ Chancellor V2 runner import failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Legacy V1 (Deprecated)
# ═══════════════════════════════════════════════════════════════════════════════

build_chancellor_graph: Any = None
chancellor_graph: Any = None


def _import_chancellor_graph() -> None:
    """Legacy V1 import - DEPRECATED, kept for fallback only."""
    global build_chancellor_graph, chancellor_graph
    if _v2_runner_available:
        return

    try:
        build_chancellor_graph = _bcg
        chancellor_graph = _cg
        logger.warning("⚠️ Using DEPRECATED V1 chancellor_graph (V2 unavailable)")
    except ImportError as e:
        logger.error(f"⚠️ Both V2 and V1 chancellor_graph unavailable: {e}")


_import_chancellor_graph()

# ═══════════════════════════════════════════════════════════════════════════════
# Exports
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Availability flags
    "_learning_loader_available",
    "_rag_shadow_available",
    "_rag_flag_available",
    "_v2_runner_available",
    "_chancellor_import_error",
    # Graph instances
    "build_chancellor_graph",
    "chancellor_graph",
    # Core imports
    "ChancellorGraph",
    "ChancellorInvokeRequest",
    "ChancellorInvokeResponse",
    "GraphState",
    "execute_node",
    "verify_node",
    "run_v2",
    "mipro_node",
    "get_antigravity_control",
    "get_system_metrics",
    "get_learning_profile",
    "get_rag_config",
    "get_shadow_metrics",
    "is_rag_shadow_enabled",
    "execute_rag_with_mode",
    "execute_rag_shadow",
    "apply_learning_profile",
    "BASE_CONFIG",
    "_get_cached_engine_status",
    "_afol_router",
    "_router",
]
