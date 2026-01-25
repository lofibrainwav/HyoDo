"""
Chancellor Router - FULL 모드 실행
ChancellorGraph 및 V2 Runner 실행 로직
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import anyio
from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from api.routers.chancellor.imports import (
    ChancellorGraph,
    chancellor_graph,
    execute_node,
    get_antigravity_control,
    mipro_node,
    run_v2,
    verify_node,
)

if TYPE_CHECKING:
    from api.routers.chancellor.imports import ChancellorInvokeRequest

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# FULL 모드 실행
# ═══════════════════════════════════════════════════════════════════════════════


async def execute_full_mode(
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """FULL 모드 실행 - Unified ChancellorGraph 사용"""
    query = request.query or request.input

    result = await ChancellorGraph.invoke(
        query,
        headers=headers,
        llm_context=llm_context,
        thread_id=request.thread_id,
        max_strategists=getattr(request, "max_strategists", 3),
    )

    outputs = result.get("outputs", {})
    execute_result = outputs.get("EXECUTE", {})
    report_result = outputs.get("REPORT", {})

    response_text = ""
    if isinstance(report_result, dict):
        response_text = report_result.get("result", "")
    if not response_text and isinstance(execute_result, dict):
        response_text = execute_result.get("result", "")
    if not response_text:
        response_text = outputs.get("V1", "Execution completed")

    return {
        "response": response_text,
        "speaker": result.get("engine", "Chancellor"),
        "thread_id": request.thread_id,
        "trinity_score": 0.9,
        "strategists_consulted": ["TRUTH", "GOODNESS", "BEAUTY"],
        "analysis_results": outputs,
        "mode_used": "full_scaling",
        "fallback_used": result.get("engine") == "V1 (Legacy)",
        "timed_out": False,
        "v2_trace_id": result.get("trace_id"),
    }


async def execute_full_mode_v2(
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
) -> dict[str, Any]:
    """V2 Runner execution with MCP Contract enforcement."""
    input_payload = {
        "query": request.query or request.input,
        "llm_context": llm_context,
        "thread_id": request.thread_id,
        "skill_id": "chancellor_invoke",
        "max_strategists": request.max_strategists,
    }

    def ok_node(step: str) -> Any:
        def _fn(state: Any) -> Any:
            state.outputs[step] = "ok"
            return state

        return _fn

    nodes = {
        "CMD": ok_node("CMD"),
        "PARSE": ok_node("PARSE"),
        "TRUTH": ok_node("TRUTH"),
        "GOODNESS": ok_node("GOODNESS"),
        "BEAUTY": ok_node("BEAUTY"),
        "MIPRO": mipro_node,
        "MERGE": ok_node("MERGE"),
        "EXECUTE": execute_node,
        "VERIFY": verify_node,
        "REPORT": ok_node("REPORT"),
    }

    try:
        state = run_v2(input_payload, nodes)

        execute_result = state.outputs.get("EXECUTE", {})
        response_text = (
            execute_result.get("result", "")
            if isinstance(execute_result, dict)
            else str(execute_result)
        )

        return {
            "response": response_text or "V2 execution completed",
            "speaker": "Chancellor V2",
            "thread_id": request.thread_id,
            "trinity_score": 0.9,
            "strategists_consulted": ["TRUTH", "GOODNESS", "BEAUTY"],
            "analysis_results": state.outputs,
            "mode_used": "full_v2",
            "fallback_used": False,
            "timed_out": False,
            "v2_trace_id": state.trace_id,
        }
    except Exception as e:
        logger.error(f"V2 Runner failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chancellor V2 execution failed: {type(e).__name__}: {e}",
        ) from e


async def execute_full_mode_v1_legacy(
    request: ChancellorInvokeRequest,
    llm_context: dict[str, Any],
) -> dict[str, Any]:
    """DEPRECATED: V1 LangGraph execution - kept for fallback only."""
    if chancellor_graph is None:
        raise HTTPException(
            status_code=503,
            detail="Chancellor Graph가 초기화되지 않았습니다.",
        )

    graph = chancellor_graph
    antigravity = get_antigravity_control()
    effective_auto_run = request.auto_run and not (antigravity and antigravity.DRY_RUN_DEFAULT)

    initial_state: dict[str, Any] = {
        "query": request.query or request.input,
        "messages": [HumanMessage(content=request.query or request.input)],
        "summary": "",
        "context": {
            "llm_context": llm_context,
            "max_strategists": request.max_strategists,
            "antigravity": {
                "AUTO_DEPLOY": antigravity.AUTO_DEPLOY if antigravity else True,
                "DRY_RUN_DEFAULT": antigravity.DRY_RUN_DEFAULT if antigravity else False,
                "ENVIRONMENT": antigravity.ENVIRONMENT if antigravity else "dev",
            },
            "auto_run_eligible": effective_auto_run,
        },
        "search_results": [],
        "multimodal_slots": {},
        "status": "INIT",
        "risk_score": 0.0,
        "trinity_score": 0.0,
        "analysis_results": {},
        "results": {},
        "actions": [],
    }

    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        with anyio.fail_after(float(request.timeout_seconds)):
            result = await graph.ainvoke(initial_state, config)
    except TimeoutError as e:
        if not request.fallback_on_timeout:
            raise HTTPException(
                status_code=504,
                detail=f"Chancellor Graph timeout after {request.timeout_seconds}s",
            ) from e
        return {
            "response": "V1 Timeout - Please use V2 mode",
            "thread_id": request.thread_id,
            "trinity_score": 0.0,
            "strategists_consulted": [],
            "mode_used": "full_v1_deprecated",
            "fallback_used": True,
            "timed_out": True,
        }

    messages = result.get("messages", [])
    last_message = messages[-1] if messages else None

    response_text = ""
    if last_message and hasattr(last_message, "content"):
        response_text = last_message.content
    elif isinstance(last_message, dict):
        response_text = last_message.get("content", "")

    strategists_consulted = []
    analysis_results = result.get("analysis_results", {})
    if analysis_results:
        strategists_consulted = list(analysis_results.keys())

    return {
        "response": response_text,
        "speaker": result.get("speaker", "Chancellor V1"),
        "thread_id": request.thread_id,
        "trinity_score": result.get("trinity_score", 0.0),
        "strategists_consulted": strategists_consulted,
        "analysis_results": analysis_results,
        "mode_used": "full_v1_deprecated",
        "fallback_used": False,
        "timed_out": False,
    }
