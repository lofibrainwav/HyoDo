"""RAG Shadow Mode - 위험 0의 프로덕션 투입 (TICKET-008 Phase 1)"""

import asyncio
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# RAG 메트릭 저장소 (메모리 기반, 프로덕션에서는 Redis/MongoDB로 교체)
_shadow_metrics = []
_metrics_lock = asyncio.Lock()


async def execute_rag_shadow(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    RAG Shadow 실행 - 사용자 응답에 영향 없음, 메트릭만 기록

    Args:
        query: 사용자 쿼리
        context: 추가 컨텍스트 (선택)

    Returns:
        메트릭 데이터 (응답 영향 없음)
    """
    start_time = time.time()
    request_id = f"shadow_{int(start_time * 1000000)}"

    try:
        from AFO.rag_engine import rag_engine

        # 실제 RAG 파이프라인 호출 (Shadow Mode)
        rag_result = await rag_engine.execute(query, context=context)

        mock_result = {
            "response": rag_result["response"],
            "confidence": rag_result["confidence"],
            "sources": rag_result["sources"],
            "latency": (time.time() - start_time),
        }

        latency_ms = (time.time() - start_time) * 1000

        # 성공 메트릭
        metrics = {
            "request_id": request_id,
            "timestamp": start_time,
            "query": query,
            "query_length": len(query),
            "latency_ms": latency_ms,
            "success": True,
            "result_summary": {
                "response_length": len(mock_result["response"]),
                "confidence": mock_result["confidence"],
                "sources_count": len(mock_result["sources"]),
                "has_sources": len(mock_result["sources"]) > 0,
            },
            "error": None,
            "context_provided": context is not None,
        }

        # 메트릭 저장
        async with _metrics_lock:
            _shadow_metrics.append(metrics)
            # 최근 1000개만 유지 (메모리 제한)
            if len(_shadow_metrics) > 1000:
                _shadow_metrics.pop(0)

        logger.info(f"RAG Shadow 성공: {request_id} ({latency_ms:.1f}ms)")
        return {"status": "success", "metrics": metrics}

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000

        # 실패 메트릭
        metrics = {
            "request_id": request_id,
            "timestamp": start_time,
            "query": query,
            "query_length": len(query),
            "latency_ms": latency_ms,
            "success": False,
            "result_summary": None,
            "error": str(e),
            "context_provided": context is not None,
        }

        # 메트릭 저장 (실패도 기록)
        async with _metrics_lock:
            _shadow_metrics.append(metrics)
            if len(_shadow_metrics) > 1000:
                _shadow_metrics.pop(0)

        logger.warning(f"RAG Shadow 실패: {request_id} ({latency_ms:.1f}ms) - {e}")
        return {"status": "error", "metrics": metrics}


async def get_shadow_metrics(limit: int = 100) -> dict[str, Any]:
    """
    Shadow 메트릭 조회

    Args:
        limit: 반환할 메트릭 개수

    Returns:
        메트릭 통계 및 최근 기록들
    """
    async with _metrics_lock:
        recent_metrics = _shadow_metrics[-limit:] if _shadow_metrics else []

        if not recent_metrics:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "recent_metrics": [],
            }

        # 통계 계산
        total = len(recent_metrics)
        successful = sum(1 for m in recent_metrics if m["success"])
        success_rate = (successful / total) * 100 if total > 0 else 0.0

        latencies = [m["latency_ms"] for m in recent_metrics if m["success"]]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "total_requests": len(_shadow_metrics),
            "recent_count": len(recent_metrics),
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(min(latencies), 2) if latencies else 0.0,
            "max_latency_ms": round(max(latencies), 2) if latencies else 0.0,
            "recent_metrics": recent_metrics,
        }


async def clear_shadow_metrics() -> dict[str, Any]:
    """Shadow 메트릭 초기화"""
    async with _metrics_lock:
        cleared_count = len(_shadow_metrics)
        _shadow_metrics.clear()

    logger.info(f"Cleared {cleared_count} shadow metrics")
    return {"cleared_count": cleared_count}


def is_rag_shadow_enabled() -> bool:
    """
    RAG Shadow 모드 활성화 여부 확인
    기본적으로 활성화 (ENV로 비활성화 가능)
    """
    return os.getenv("AFO_RAG_SHADOW_ENABLED", "1").lower() in ("1", "true", "yes")
