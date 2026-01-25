"""
Chancellor Router - 실행 함수들
모드별 실행 로직 (offline, fast, lite, full)

Refactored (Phase 73):
- full_mode.py: FULL 모드 실행 로직
- v2_routing.py: V2/Shadow 모드 라우팅 로직
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

import anyio
from fastapi import HTTPException

from api.routers.chancellor.full_mode import (
    execute_full_mode,
    execute_full_mode_v1_legacy,
    execute_full_mode_v2,
)
from api.routers.chancellor.helpers import (
    build_fallback_text,
    determine_v2_routing,
    is_real_answer,
)
from api.routers.chancellor.imports import (
    ChancellorInvokeRequest,
    _afol_router,
    _rag_flag_available,
    _rag_shadow_available,
    _router,
    _v2_runner_available,
    execute_rag_shadow,
    execute_rag_with_mode,
    get_system_metrics,
    is_rag_shadow_enabled,
)
from api.routers.chancellor.v2_routing import (
    SHADOW_DIFF_DIR,
    _execute_shadow_mode,
    _execute_v2_with_fallback,
    _find_project_root,
    _save_shadow_diff,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 시스템 메트릭 수집
# ═══════════════════════════════════════════════════════════════════════════════


async def _get_system_metrics_safe() -> dict[str, Any]:
    """시스템 메트릭 안전하게 수집"""
    try:
        return dict(await get_system_metrics())
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning("시스템 메트릭 수집 실패 (속성/타입/값 에러): %s", str(e))
        return {"error": f"failed to collect system metrics: {type(e).__name__}: {e}"}
    except Exception as e:
        logger.warning("시스템 메트릭 수집 실패 (예상치 못한 에러): %s", str(e))
        return {"error": f"failed to collect system metrics: {type(e).__name__}: {e}"}


# ═══════════════════════════════════════════════════════════════════════════════
# Single Shot 실행
# ═══════════════════════════════════════════════════════════════════════════════


async def _single_shot_answer(
    query: str,
    budget_seconds: float,
    context: dict[str, Any],
) -> tuple[str, dict[str, Any] | None, bool]:
    """단일 LLM 호출"""
    router = _router if _router else _afol_router

    timed_out = False
    try:
        with anyio.fail_after(max(0.5, budget_seconds)):
            result = await router.execute_with_routing(query, context=context)
        return result.get("response", ""), result.get("routing"), timed_out
    except TimeoutError:
        timed_out = True
        return "", None, timed_out


# ═══════════════════════════════════════════════════════════════════════════════
# 메인 실행 함수
# ═══════════════════════════════════════════════════════════════════════════════


async def execute_with_fallback(
    mode_used: Literal["offline", "fast", "lite", "full"],
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    실행 모드에 따른 처리 및 폴백 (Phase 23-24 V2 라우팅 지원).

    V2 라우팅 우선순위:
    1. X-AFO-Engine 헤더 (v2, v1, shadow)
    2. Canary 퍼센트 (랜덤 트래픽 분배)
    3. Shadow 모드 (V2 백그라운드 실행)

    Args:
        mode_used: 실행 모드
        request: Chancellor 요청
        llm_context: LLM 컨텍스트
        headers: HTTP 헤더

    Returns:
        처리 결과
    """
    query = request.query or request.input

    # TICKET-008 Phase 3: RAG 통합 실행
    if _rag_flag_available:
        await execute_rag_with_mode(
            query,
            headers,
            {
                "llm_context": llm_context,
                "thread_id": request.thread_id,
                "mode_used": mode_used,
            },
        )

    # TICKET-008 Phase 1: RAG Shadow 실행
    if _rag_shadow_available and is_rag_shadow_enabled():
        asyncio.create_task(
            execute_rag_shadow(
                query,
                {"llm_context": llm_context, "thread_id": request.thread_id},
            )
        )

    # OFFLINE 모드
    if mode_used == "offline":
        metrics = await _get_system_metrics_safe()
        return {
            "response": build_fallback_text(query, metrics),
            "thread_id": request.thread_id,
            "trinity_score": 0.0,
            "strategists_consulted": [],
            "mode_used": mode_used,
            "fallback_used": True,
            "timed_out": False,
            "system_metrics": metrics,
        }

    # FAST/LITE 모드
    if mode_used in {"fast", "lite"}:
        return await _execute_fast_lite_mode(mode_used, request, llm_context)

    # FULL 모드 - V2 라우팅 결정 (Phase 23-24)
    v2_routing = determine_v2_routing(headers, _v2_runner_available)
    logger.info(f"🎯 V2 라우팅 결정: {v2_routing}")

    # Shadow 모드: V2를 백그라운드에서 실행, V1 응답 반환
    if v2_routing.shadow_mode and _v2_runner_available:
        return await _execute_shadow_mode(request, llm_context, headers, v2_routing)

    # V2 직접 실행
    if v2_routing.use_v2:
        return await _execute_v2_with_fallback(request, llm_context, v2_routing)

    # V1 실행 (기본)
    return await execute_full_mode(request, llm_context, headers)


async def _execute_fast_lite_mode(
    mode_used: Literal["fast", "lite"],
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
) -> dict[str, Any]:
    """FAST/LITE 모드 실행"""
    query = request.query or request.input
    budget_total = float(request.timeout_seconds)
    budget_llm = max(0.5, budget_total - 1.0)

    # 모드별 기본값 설정
    if mode_used == "fast":
        llm_context.setdefault("max_tokens", 128)
        llm_context.setdefault("temperature", 0.2)
        llm_context.setdefault("ollama_timeout_seconds", budget_llm)
        llm_context.setdefault("ollama_num_ctx", 2048)
    else:
        llm_context.setdefault("max_tokens", 384)
        llm_context.setdefault("temperature", 0.4)
        llm_context.setdefault("ollama_timeout_seconds", budget_llm)
        llm_context.setdefault("ollama_num_ctx", 4096)

    answer, routing, timed_out = await _single_shot_answer(query, budget_llm, llm_context)

    if is_real_answer(answer, routing):
        return {
            "response": answer,
            "thread_id": request.thread_id,
            "trinity_score": 0.0,
            "strategists_consulted": ["single_shot"],
            "mode_used": mode_used,
            "fallback_used": False,
            "timed_out": timed_out,
            "routing": routing,
        }

    if not request.fallback_on_timeout:
        raise HTTPException(
            status_code=504,
            detail=f"Chancellor LLM timeout after {request.timeout_seconds}s",
        )

    metrics = await _get_system_metrics_safe()
    return {
        "response": build_fallback_text(query, metrics),
        "thread_id": request.thread_id,
        "trinity_score": 0.0,
        "strategists_consulted": [],
        "mode_used": mode_used,
        "fallback_used": True,
        "timed_out": True,
        "system_metrics": metrics,
        "routing": routing,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Re-exports for backward compatibility
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Main entry point
    "execute_with_fallback",
    # Internal helpers (exposed for testing)
    "_get_system_metrics_safe",
    "_single_shot_answer",
    "_execute_fast_lite_mode",
    # Re-exports from full_mode.py
    "execute_full_mode",
    "execute_full_mode_v2",
    "execute_full_mode_v1_legacy",
    # Re-exports from v2_routing.py
    "_execute_shadow_mode",
    "_execute_v2_with_fallback",
    "_save_shadow_diff",
    "_find_project_root",
    "SHADOW_DIFF_DIR",
]
