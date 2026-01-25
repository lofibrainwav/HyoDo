"""
Chancellor Router - V2 라우팅 실행
V2/Shadow 모드 라우팅 및 Diff 분석 로직 (Phase 23-24)
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException

from AFO.config.settings import get_settings
from api.routers.chancellor.helpers import V2RoutingDecision, get_v2_settings

if TYPE_CHECKING:
    from api.routers.chancellor.imports import ChancellorInvokeRequest

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Shadow Diff 저장 경로 (SSOT: PH22_03_V2_CUTOVER_SSOT.md)
# ═══════════════════════════════════════════════════════════════════════════════


def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml or use /app for Docker."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # Docker fallback: /app is the root in container
    if Path("/app").exists() and Path("/app/AFO").exists():
        return Path("/app").parent  # Return parent so artifacts/ is at same level
    return current.parents[min(5, len(current.parents) - 1)]


_PROJECT_ROOT = _find_project_root()
SHADOW_DIFF_DIR = _PROJECT_ROOT / "artifacts" / "chancellor_shadow_diff"


# ═══════════════════════════════════════════════════════════════════════════════
# Shadow Diff 저장 (Phase 24)
# ═══════════════════════════════════════════════════════════════════════════════


async def _save_shadow_diff(
    query: str,
    v1_result: dict[str, Any],
    v2_result: dict[str, Any],
) -> None:
    """
    Shadow 모드 Diff 분석 저장 (Phase 24).

    V1과 V2 실행 결과를 비교하여 artifacts에 저장.
    샘플링 비율에 따라 저장 여부 결정.
    """
    settings = get_settings()
    sampling_rate = settings.CHANCELLOR_V2_DIFF_SAMPLING_RATE

    # 샘플링 체크
    if random.random() > sampling_rate:
        logger.debug(f"🌓 Shadow Diff 샘플링 스킵 (rate={sampling_rate})")
        return

    try:
        # Diff Evidence 생성
        diff_entry = {
            "timestamp": time.time(),
            "input": query,
            "v1_engine": v1_result.get("speaker", "Chancellor V1"),
            "v1_success": not v1_result.get("fallback_used", False),
            "v1_response_len": len(v1_result.get("response", "")),
            "v2_trace_id": v2_result.get("v2_trace_id"),
            "v2_success": not v2_result.get("fallback_used", False),
            "v2_response_len": len(v2_result.get("response", "")),
            "v2_error_count": 0 if v2_result.get("v2_trace_id") else 1,
            "trinity_score_diff": abs(
                v2_result.get("trinity_score", 0) - v1_result.get("trinity_score", 0)
            ),
        }

        # artifacts 디렉토리 생성
        SHADOW_DIFF_DIR.mkdir(parents=True, exist_ok=True)

        # 파일명: trace_id 기반 또는 timestamp
        trace_id = v2_result.get("v2_trace_id") or int(time.time())
        filename = f"diff_{trace_id}.json"
        filepath = SHADOW_DIFF_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(diff_entry, f, indent=2)

        logger.info(f"🌓 Shadow Diff 저장 완료: {filename}")

    except Exception as e:
        # Shadow 모드 실패는 프로덕션에 영향을 주지 않도록 조용히 실패
        logger.warning(f"🌓 Shadow Diff 저장 실패 (무시됨): {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Shadow 모드 실행
# ═══════════════════════════════════════════════════════════════════════════════


async def _execute_shadow_mode(
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
    headers: dict[str, str] | None,
    v2_routing: V2RoutingDecision,
) -> dict[str, Any]:
    """
    Shadow 모드 실행: V2를 백그라운드에서 실행하고 V1 응답을 반환.

    V2 결과는 백그라운드에서 수집되어 Diff 분석에 사용됨.
    """
    # Deferred import to avoid circular dependency
    from api.routers.chancellor.full_mode import execute_full_mode, execute_full_mode_v2

    logger.info(f"🌓 Shadow 모드 실행 시작: {v2_routing.reason}")
    query = request.query or request.input

    # V1 응답 먼저 실행 (사용자에게 반환)
    v1_result = await execute_full_mode(request, llm_context, headers)
    v1_result["shadow_mode"] = True
    v1_result["routing_reason"] = v2_routing.reason

    # V2를 백그라운드에서 실행 (결과는 Diff 분석용)
    async def _run_v2_shadow() -> dict[str, Any] | None:
        try:
            v2_result = await execute_full_mode_v2(request, llm_context)
            logger.info(f"🌓 Shadow V2 완료: trace_id={v2_result.get('v2_trace_id')}")

            # Phase 24: Diff 분석 저장
            await _save_shadow_diff(query, v1_result, v2_result)
            return v2_result
        except Exception as e:
            logger.warning(f"🌓 Shadow V2 실패 (무시됨): {e}")
            return None

    # 백그라운드 태스크 생성
    asyncio.create_task(_run_v2_shadow())

    return v1_result


# ═══════════════════════════════════════════════════════════════════════════════
# V2 실행 with V1 폴백
# ═══════════════════════════════════════════════════════════════════════════════


async def _execute_v2_with_fallback(
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
    v2_routing: V2RoutingDecision,
) -> dict[str, Any]:
    """
    V2 실행 with V1 폴백.

    V2 실행 실패 시 설정에 따라 V1으로 폴백.
    """
    # Deferred import to avoid circular dependency
    from api.routers.chancellor.full_mode import execute_full_mode, execute_full_mode_v2

    logger.info(f"🚀 V2 직접 실행: {v2_routing.reason}")
    settings = get_v2_settings()

    try:
        result = await execute_full_mode_v2(request, llm_context)
        result["routing_reason"] = v2_routing.reason
        return result
    except Exception as e:
        logger.error(f"V2 실행 실패: {e}")

        # V1으로 폴백 허용 여부 확인
        if settings["fallback_to_v1"]:
            logger.warning("⚠️ V2 실패, V1으로 폴백")
            v1_result = await execute_full_mode(request, llm_context, None)
            v1_result["v2_error"] = str(e)
            v1_result["fallback_used"] = True
            v1_result["routing_reason"] = f"{v2_routing.reason} -> V1 fallback"
            return v1_result

        # 폴백 비활성화 시 에러 전파
        raise HTTPException(
            status_code=500,
            detail=f"Chancellor V2 failed (fallback disabled): {type(e).__name__}: {e}",
        ) from e
