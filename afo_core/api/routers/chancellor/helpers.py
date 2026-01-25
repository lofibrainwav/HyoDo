"""
Chancellor Router - 헬퍼 함수들
실행 모드 결정, LLM 컨텍스트 구축, 폴백 텍스트 생성
V2 라우팅 로직 (Phase 23-24)
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

if TYPE_CHECKING:
    from AFO.api.compat import ChancellorInvokeRequest

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 시스템 쿼리 키워드
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_QUERY_KEYWORDS = [
    "상태",
    "health",
    "헬스",
    "metrics",
    "메트릭",
    "redis",
    "postgres",
    "postgresql",
    "db",
    "데이터베이스",
    "포트",
    "서버",
    "메모리",
    "스왑",
    "디스크",
    "오장육부",
    "langgraph",
    "엔드포인트",
]


def _looks_like_system_query(query: str) -> bool:
    """시스템 관련 쿼리인지 확인"""
    q = query.lower()
    return any(k in q for k in SYSTEM_QUERY_KEYWORDS)


# ═══════════════════════════════════════════════════════════════════════════════
# 실행 모드 결정
# ═══════════════════════════════════════════════════════════════════════════════


def determine_execution_mode(
    request: ChancellorInvokeRequest,
) -> Literal["offline", "fast", "lite", "full"]:
    """
    실행 모드 결정 (美: 순수 함수 - 동일 입력에 동일 출력)

    Args:
        request: Chancellor 요청

    Returns:
        결정된 실행 모드
    """
    query_text = request.query or request.input

    if request.mode == "auto":
        if _looks_like_system_query(query_text):
            return "offline"
        elif request.timeout_seconds <= 12:
            return "fast"
        elif request.timeout_seconds <= 45:
            return "lite"
        else:
            return "full"
    else:
        mode = request.mode
        if mode in ["offline", "fast", "lite", "full"]:
            return cast("Literal['offline', 'fast', 'lite', 'full']", mode)
        return "full"


# ═══════════════════════════════════════════════════════════════════════════════
# LLM 컨텍스트 구축
# ═══════════════════════════════════════════════════════════════════════════════


def build_llm_context(request: ChancellorInvokeRequest) -> dict[str, Any]:
    """
    LLM 컨텍스트 구축 (美: 순수 함수)

    Args:
        request: Chancellor 요청

    Returns:
        LLM 컨텍스트 딕셔너리
    """
    llm_context: dict[str, Any] = {}

    if request.provider != "auto":
        llm_context["provider"] = request.provider
    if request.ollama_model:
        llm_context["ollama_model"] = request.ollama_model
    if request.ollama_timeout_seconds is not None:
        llm_context["ollama_timeout_seconds"] = request.ollama_timeout_seconds
    if request.ollama_num_ctx is not None:
        llm_context["ollama_num_ctx"] = request.ollama_num_ctx
    if request.ollama_num_thread is not None:
        llm_context["ollama_num_thread"] = request.ollama_num_thread
    if request.max_tokens is not None:
        llm_context["max_tokens"] = request.max_tokens
    if request.temperature is not None:
        llm_context["temperature"] = request.temperature

    return llm_context


# ═══════════════════════════════════════════════════════════════════════════════
# 폴백 텍스트 생성
# ═══════════════════════════════════════════════════════════════════════════════


def build_fallback_text(query: str, metrics: dict[str, Any]) -> str:
    """Build fallback text for offline mode responses."""
    is_system = _looks_like_system_query(query)

    mem = metrics.get("memory_percent")
    swap = metrics.get("swap_percent")
    disk = metrics.get("disk_percent")
    redis_ok = metrics.get("redis_connected")
    langgraph_ok = metrics.get("langgraph_active")
    containers = metrics.get("containers_running")

    lines = [
        "승상 보고(폴백 모드): LLM 응답이 지연되어 현재는 제한된 방식으로 답변합니다.",
        "",
        f"- 요청: {query}",
    ]

    if is_system:
        lines.extend(
            [
                f"- 메모리: {mem}%",
                f"- 스왑: {swap}%",
                f"- 디스크: {disk}%",
                f"- Redis: {'연결됨' if redis_ok else '미연결'}",
                f"- LangGraph: {'활성' if langgraph_ok else '비활성'}",
                f"- 감지된 서비스(추정): {containers}",
            ]
        )
    else:
        q_lower = query.lower()
        if any(k in q_lower for k in ["자기소개", "who are you", "너는 누구", "당신은 누구"]):
            lines.append(
                "- 오프라인 응답: 저는 AFO Kingdom의 승상(Chancellor)이며, "
                "시스템 상태/전략/실행을 정리해 사령관의 결정을 돕습니다."
            )
        else:
            lines.append(
                "- 오프라인 응답: 현재 LLM이 제시간에 응답하지 못해 "
                "질문에 대한 생성형 답변을 확정할 수 없습니다."
            )

    lines.extend(
        [
            "",
            "504를 줄이고 실제 LLM 답변 확률을 올리려면:",
            "- `mode=fast` 또는 `mode=lite`로 LLM 호출 수를 1회로 제한",
            "- 더 작은(빠른) 모델 사용: `ollama_model` (예: `llama3.2:3b`, `qwen2.5:3b`)",
            "- Ollama 성능 옵션: `ollama_num_ctx`(예: 2048~4096), `ollama_num_thread`",
            "- 시간 예산 확대: `timeout_seconds` (예: 20~60초)",
        ]
    )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 응답 검증
# ═══════════════════════════════════════════════════════════════════════════════


def is_real_answer(answer: str, routing: dict[str, Any] | None) -> bool:
    """Check if the answer is a real LLM response (not fallback)."""
    text = (answer or "").strip()
    if not text:
        return False
    if routing and routing.get("is_fallback") is True:
        return False
    lowered = text.lower()
    return not (
        text.lstrip().startswith("[")
        and (
            " error" in lowered
            or lowered.startswith("[fallback")
            or "unavailable" in lowered
            or "api wrapper unavailable" in lowered
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# V2 라우팅 로직 (Phase 23-24)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class V2RoutingDecision:
    """V2 라우팅 결정 결과."""

    use_v2: bool
    shadow_mode: bool
    reason: str


def get_v2_settings() -> dict[str, Any]:
    """V2 라우팅 설정 로드."""
    try:
        from config.settings import get_settings

        settings = get_settings()
        return {
            "enabled": settings.CHANCELLOR_V2_ENABLED,
            "header_routing": settings.CHANCELLOR_V2_HEADER_ROUTING,
            "canary_percent": settings.CHANCELLOR_V2_CANARY_PERCENT,
            "shadow_mode": settings.CHANCELLOR_V2_SHADOW_MODE,
            "fallback_to_v1": settings.CHANCELLOR_V2_FALLBACK_TO_V1,
        }
    except Exception as e:
        logger.warning(f"V2 설정 로드 실패, 기본값 사용: {e}")
        return {
            "enabled": True,
            "header_routing": True,
            "canary_percent": 0,
            "shadow_mode": False,
            "fallback_to_v1": True,
        }


def determine_v2_routing(
    headers: dict[str, str] | None = None,
    v2_available: bool = True,
) -> V2RoutingDecision:
    """
    V2 라우팅 결정 (Phase 23-24 Strangler Fig Pattern).

    라우팅 우선순위:
    1. X-AFO-Engine 헤더 (v2, v1, shadow)
    2. Canary 퍼센트 (랜덤 트래픽 분배)
    3. Shadow 모드 (V2 백그라운드 실행)

    Args:
        headers: HTTP 요청 헤더
        v2_available: V2 runner 사용 가능 여부

    Returns:
        V2RoutingDecision 객체
    """
    settings = get_v2_settings()

    # V2 비활성화 또는 불가능
    if not settings["enabled"] or not v2_available:
        return V2RoutingDecision(
            use_v2=False,
            shadow_mode=False,
            reason="V2 disabled or unavailable",
        )

    # 1. 헤더 기반 라우팅 (최우선)
    if settings["header_routing"] and headers:
        engine_header = headers.get("x-afo-engine", "").lower()

        if engine_header == "v2":
            logger.info("🎯 V2 라우팅: X-AFO-Engine 헤더")
            return V2RoutingDecision(
                use_v2=True,
                shadow_mode=False,
                reason="header: X-AFO-Engine=v2",
            )
        elif engine_header == "v1":
            logger.info("🎯 V1 라우팅: X-AFO-Engine 헤더")
            return V2RoutingDecision(
                use_v2=False,
                shadow_mode=False,
                reason="header: X-AFO-Engine=v1",
            )
        elif engine_header == "shadow":
            logger.info("🎯 Shadow 라우팅: X-AFO-Engine 헤더")
            return V2RoutingDecision(
                use_v2=False,
                shadow_mode=True,
                reason="header: X-AFO-Engine=shadow",
            )

    # 2. Canary 모드 (퍼센트 기반)
    canary_percent = settings["canary_percent"]
    if canary_percent > 0:
        roll = random.randint(1, 100)
        if roll <= canary_percent:
            logger.info(f"🎯 V2 Canary 라우팅: roll={roll} <= {canary_percent}%")
            return V2RoutingDecision(
                use_v2=True,
                shadow_mode=False,
                reason=f"canary: {canary_percent}% (roll={roll})",
            )

    # 3. Shadow 모드 (전역 설정)
    if settings["shadow_mode"]:
        logger.info("🎯 Shadow 모드 활성화 (전역 설정)")
        return V2RoutingDecision(
            use_v2=False,
            shadow_mode=True,
            reason="config: shadow_mode=True",
        )

    # 기본: V1 사용
    return V2RoutingDecision(
        use_v2=False,
        shadow_mode=False,
        reason="default: V1",
    )
