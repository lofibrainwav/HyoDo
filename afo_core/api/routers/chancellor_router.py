"""
Chancellor Router (호환성 유지를 위한 Re-exports)

리팩터링: 500줄 규칙 준수를 위해 chancellor/ 패키지로 분리
기존 import 경로 호환성 유지

실제 구현:
- api/routers/chancellor/imports.py: 공통 import
- api/routers/chancellor/helpers.py: 헬퍼 함수들
- api/routers/chancellor/executors.py: 실행 함수들
- api/routers/chancellor/router.py: API 엔드포인트
"""

# Re-export router for backwards compatibility
# Re-export commonly used items
from api.routers.chancellor.executors import (
    execute_full_mode,
    execute_full_mode_v1_legacy,
    execute_full_mode_v2,
    execute_with_fallback,
)
from api.routers.chancellor.helpers import (
    build_fallback_text,
    build_llm_context,
    determine_execution_mode,
    is_real_answer,
)

# Backwards compatibility aliases (테스트 호환성)
_build_llm_context = build_llm_context
_build_fallback_text = build_fallback_text
_determine_execution_mode = determine_execution_mode
_execute_with_fallback = execute_with_fallback
from api.routers.chancellor.imports import (
    ChancellorGraph,
    ChancellorInvokeRequest,
    ChancellorInvokeResponse,
    _learning_loader_available,
    _rag_flag_available,
    _rag_shadow_available,
    _v2_runner_available,
    chancellor_graph,
)
from api.routers.chancellor.router import router

__all__ = [
    # Router
    "router",
    # Types
    "ChancellorInvokeRequest",
    "ChancellorInvokeResponse",
    "ChancellorGraph",
    # Flags
    "_learning_loader_available",
    "_rag_shadow_available",
    "_rag_flag_available",
    "_v2_runner_available",
    # Graph
    "chancellor_graph",
    # Helpers
    "determine_execution_mode",
    "build_llm_context",
    "build_fallback_text",
    "is_real_answer",
    # Executors
    "execute_with_fallback",
    "execute_full_mode",
    "execute_full_mode_v2",
    "execute_full_mode_v1_legacy",
    # Backwards compatibility aliases
    "_build_llm_context",
    "_build_fallback_text",
    "_determine_execution_mode",
    "_execute_with_fallback",
]
