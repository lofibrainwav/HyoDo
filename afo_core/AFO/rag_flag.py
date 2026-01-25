"""RAG Flag Mode + Gradual Mode - 선택적 RAG 적용 (TICKET-008 Phase 2 + 3)"""

import asyncio
import hashlib
import os
from contextlib import asynccontextmanager
from typing import Any

# RAG 동시성 제한을 위한 세마포어
_rag_semaphore: asyncio.Semaphore | None = None


def init_rag_semaphore() -> None:
    """RAG 동시성 제한 세마포어 초기화"""
    global _rag_semaphore
    max_concurrency = int(os.getenv("AFO_RAG_MAX_CONCURRENCY", "8"))
    _rag_semaphore = asyncio.Semaphore(max_concurrency)


def is_rag_flag_enabled(request_headers: dict[str, str] | None = None) -> bool:
    """
    RAG Flag 모드 활성화 여부 확인

    우선순위:
    1. 헤더: X-AFO-RAG: 1 (가장 우선)
    2. ENV: AFO_RAG_FLAG_ENABLED=1 (기본값: 0)

    Args:
        request_headers: HTTP 요청 헤더

    Returns:
        Flag 모드 활성화 여부
    """
    # 헤더 우선 확인
    if request_headers and request_headers.get("x-afo-rag") == "1":
        return True

    # ENV 확인
    return os.getenv("AFO_RAG_FLAG_ENABLED", "0").lower() in ("1", "true", "yes")


def get_rag_config() -> dict[str, Any]:
    """
    RAG 설정 조회

    Returns:
        RAG 관련 설정들
    """
    return {
        "flag_enabled": os.getenv("AFO_RAG_FLAG_ENABLED", "0"),
        "timeout_ms": int(os.getenv("AFO_RAG_TIMEOUT_MS", "1000")),
        "max_concurrency": int(os.getenv("AFO_RAG_MAX_CONCURRENCY", "8")),
        "shadow_enabled": os.getenv("AFO_RAG_SHADOW_ENABLED", "1"),
    }


@asynccontextmanager
async def rag_semaphore_context():
    """
    RAG 동시성 제한 컨텍스트 매니저

    Usage:
        async with rag_semaphore_context():
            result = await execute_rag(query)
    """
    global _rag_semaphore
    if _rag_semaphore is None:
        init_rag_semaphore()

    async with _rag_semaphore:
        yield


async def execute_rag_with_flag(
    query: str,
    request_headers: dict[str, str] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Flag 모드 기반 RAG 실행

    Args:
        query: 사용자 쿼리
        request_headers: HTTP 요청 헤더
        context: 추가 컨텍스트

    Returns:
        RAG 실행 결과 또는 fallback 정보
    """
    from AFO.rag_shadow import execute_rag_shadow

    start_time = asyncio.get_event_loop().time()
    flag_enabled = is_rag_flag_enabled(request_headers)
    config = get_rag_config()

    result = {
        "mode": "flag" if flag_enabled else "shadow",
        "flag_enabled": flag_enabled,
        "config": config,
        "applied": False,
        "fallback_reason": None,
        "rag_result": None,
        "shadow_result": None,
        "latency_ms": 0.0,
    }

    try:
        if flag_enabled:
            # Flag ON: 동기 실행 + timeout
            timeout_seconds = config["timeout_ms"] / 1000.0

            async with rag_semaphore_context():
                try:
                    from AFO.rag_engine import rag_engine

                    rag_result = await asyncio.wait_for(
                        rag_engine.execute(query, context=context),
                        timeout=timeout_seconds,
                    )

                    result["applied"] = True
                    result["rag_result"] = rag_result

                except TimeoutError:
                    result["fallback_reason"] = "timeout"
                except Exception as e:
                    result["fallback_reason"] = f"error: {e!s}"

        # Shadow는 항상 실행 (응답 영향 없음)
        asyncio.create_task(execute_rag_shadow(query, context))
        result["shadow_task_created"] = True

        # 결과 요약
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        result["latency_ms"] = round(latency_ms, 2)

        return result

    except Exception as e:
        # 최종 fallback
        result["fallback_reason"] = f"system_error: {e!s}"
        result["latency_ms"] = round((asyncio.get_event_loop().time() - start_time) * 1000, 2)
        return result


# TICKET-008 Phase 3: Gradual Mode
def determine_rag_mode(request_headers: dict[str, str] | None = None) -> dict[str, Any]:
    """
    RAG 적용 모드 결정 - 우선순위 순서대로 평가 (TICKET-008 Phase 3)

    우선순위 (높은 순):
    1. KILL_SWITCH (무조건 OFF)
    2. X-AFO-RAG 헤더 (1=강제ON, 0=강제OFF)
    3. FLAG ENV (AFO_RAG_FLAG_ENABLED)
    4. GRADUAL ENV (AFO_RAG_ROLLOUT_*)
    5. 기본값: SHADOW_ONLY
    """
    # Normalize headers to lowercase for case-insensitive lookup
    headers = {k.lower(): v for k, v in (request_headers or {}).items()}

    # 1. Kill Switch (최우선)
    if os.getenv("AFO_RAG_KILL_SWITCH", "0") == "1":
        return {"mode": "killed", "applied": False, "reason": "kill_switch_active"}

    # 2. 강제 헤더 (X-AFO-RAG: 1/0)
    rag_header = headers.get("x-afo-rag")
    if rag_header == "1":
        return {"mode": "forced_on", "applied": True, "reason": "header_forced"}
    elif rag_header == "0":
        return {"mode": "forced_off", "applied": False, "reason": "header_forced"}

    # 3. Flag ENV
    if os.getenv("AFO_RAG_FLAG_ENABLED", "0") == "1":
        return {"mode": "flag", "applied": True, "reason": "flag_enabled"}

    # 4. Gradual Rollout
    if os.getenv("AFO_RAG_ROLLOUT_ENABLED", "0") == "1":
        percent = int(os.getenv("AFO_RAG_ROLLOUT_PERCENT", "0"))
        if percent > 0:
            # 버킷팅 결정
            bucket_seed = get_bucket_seed(request_headers)
            applied = should_apply_gradual(bucket_seed, percent)
            return {
                "mode": "gradual",
                "applied": applied,
                "rollout_percent": percent,
                "bucket_seed": bucket_seed,
                "bucket_seed_source": get_bucket_seed_source(request_headers),
                "reason": f"gradual_{percent}pct",
            }

    # 5. 기본값: Shadow Only
    return {"mode": "shadow_only", "applied": False, "reason": "default_shadow"}


def get_bucket_seed(headers: dict[str, str] | None) -> str:
    """
    안정적인 버킷팅을 위한 seed 생성

    우선순위:
    1. X-AFO-CLIENT-ID
    2. X-Request-ID
    3. remote_addr + user_agent (실제 구현시)
    """
    # Normalize headers to lowercase for case-insensitive lookup
    normalized = {k.lower(): v for k, v in (headers or {}).items()}

    # 1순위: X-AFO-CLIENT-ID
    if "x-afo-client-id" in normalized:
        return normalized["x-afo-client-id"]

    # 2순위: X-Request-ID
    if "x-request-id" in normalized:
        return normalized["x-request-id"]

    # 3순위: 기본 seed (실제 구현시 IP + User-Agent 사용)
    return "default_seed"


def get_bucket_seed_source(headers: dict[str, str] | None) -> str:
    """버킷팅 seed 출처 반환"""
    # Normalize headers to lowercase for case-insensitive lookup
    normalized = {k.lower(): v for k, v in (headers or {}).items()}

    if "x-afo-client-id" in normalized:
        return "client_id"
    if "x-request-id" in normalized:
        return "request_id"

    return "default"


def should_apply_gradual(seed: str, percent: int) -> bool:
    """
    해시 기반 결정 (동일 seed는 항상 같은 결과)

    Args:
        seed: 버킷팅용 시드
        percent: 적용 비율 (0-100)

    Returns:
        적용 여부
    """
    import hashlib

    hash_value = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return (hash_value % 100) < percent


async def execute_rag_with_mode(
    query: str,
    request_headers: dict[str, str] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    통합 RAG 실행 (Shadow + Flag + Gradual) - TICKET-008 Phase 3

    Args:
        query: 사용자 쿼리
        request_headers: HTTP 요청 헤더
        context: 추가 컨텍스트

    Returns:
        RAG 실행 결과 + 결정 메트릭
    """
    from AFO.rag_shadow import execute_rag_shadow

    start_time = asyncio.get_event_loop().time()

    # 모드 결정
    mode_decision = determine_rag_mode(request_headers)
    config = get_rag_config()

    result = {
        "decision_mode": mode_decision["mode"],
        "applied": mode_decision["applied"],
        "reason": mode_decision["reason"],
        "config": config,
        "fallback_reason": None,
        "rag_result": None,
        "shadow_result": None,
        "latency_ms": 0.0,
    }

    # Gradual 모드 추가 정보
    if mode_decision["mode"] == "gradual":
        # 보안: bucket_seed 원문 대신 해시만 저장
        bucket_seed = mode_decision.get("bucket_seed", "")
        result.update(
            {
                "rollout_percent": mode_decision.get("rollout_percent", 0),
                "bucket_id": (
                    hashlib.sha256(bucket_seed.encode()).hexdigest()[:8] if bucket_seed else ""
                ),
                "bucket_seed_source": mode_decision.get("bucket_seed_source", ""),
            }
        )

    try:
        if mode_decision["applied"]:
            # RAG 적용: 동기 실행 + timeout
            timeout_seconds = config["timeout_ms"] / 1000.0

            async with rag_semaphore_context():
                try:
                    from AFO.rag_engine import rag_engine

                    rag_result = await asyncio.wait_for(
                        rag_engine.execute(query, context=context),
                        timeout=timeout_seconds,
                    )

                    result["rag_result"] = rag_result

                except TimeoutError:
                    result["fallback_reason"] = "timeout"
                    result["applied"] = False  # fallback으로 변경
                except Exception as e:
                    result["fallback_reason"] = f"error: {e!s}"
                    result["applied"] = False  # fallback으로 변경

        # Shadow는 항상 실행 (응답 영향 없음)
        asyncio.create_task(execute_rag_shadow(query, context))
        result["shadow_task_created"] = True

        # 결과 요약
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        result["latency_ms"] = round(latency_ms, 2)

        return result

    except Exception as e:
        # 최종 fallback
        result["fallback_reason"] = f"system_error: {e!s}"
        result["applied"] = False
        result["latency_ms"] = round((asyncio.get_event_loop().time() - start_time) * 1000, 2)
        return result
