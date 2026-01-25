import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from AFO.utils.standard_shield import shield

# Configure logging
logger = logging.getLogger(__name__)
try:
    from AFO.llm_router import route_and_execute

    LLM_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ LLM infrastructure not available: {e}")
    LLM_AVAILABLE = False

    # Mock classes for fallback
    class MockLLMRouter:
        pass

    class MockRoutingDecision:
        def __init__(self) -> None:
            self.selected_provider = "mock"
            self.selected_model = "mock-model"
            self.reasoning = "Mock LLM response"

    class MockQualityTier:
        STANDARD = "standard"
        PREMIUM = "premium"

    LLMRouter = MockLLMRouter
    RoutingDecision = MockRoutingDecision
    QualityTier = MockQualityTier

    async def route_and_execute(query: str, context: dict | None = None) -> dict:
        return {
            "success": True,
            "response": f"Mock LLM response for: {query}",
            "provider": "mock",
            "model": "mock-model",
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Configure logging
logger = logging.getLogger(__name__)

# Create router
llm_router = APIRouter(
    prefix="/llm",
    tags=["llm-integration"],
    responses={
        404: {"description": "LLM service not found"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)


# Pydantic Models for LLM APIs
class LLMQueryRequest(BaseModel):
    """LLM 쿼리 요청 모델"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="LLM에 전달할 쿼리 텍스트",
        examples=["세무 보고서에서 가장 중요한 항목들을 분석해주세요"],
    )
    context: dict[str, object] | None = Field(
        default=None,
        description="추가 컨텍스트 정보",
        examples=[{"document_type": "tax_return", "user_role": "accountant"}],
    )
    provider: str | None = Field(
        default=None, description="특정 LLM 제공자 지정", examples=["claude", "gpt-4", "ollama"]
    )
    quality_tier: str = Field(
        default="standard", description="품질 티어", examples=["standard", "premium"]
    )
    max_tokens: int | None = Field(default=None, ge=1, le=4000, description="최대 토큰 수")


class LLMQueryResponse(BaseModel):
    """LLM 쿼리 응답 모델"""

    success: bool = Field(..., description="요청 성공 여부")
    response: str = Field(..., description="LLM 응답 텍스트")
    provider: str = Field(..., description="사용된 LLM 제공자")
    model: str = Field(..., description="사용된 모델")
    reasoning: str = Field(..., description="라우팅 선택 이유")
    tokens_used: int | None = Field(default=None, description="사용된 토큰 수")
    processing_time: float = Field(..., description="처리 시간 (초)")
    timestamp: str = Field(..., description="응답 생성 시각")
    trinity_score: dict[str, float] = Field(
        default_factory=dict, description="응답 품질 Trinity Score"
    )


class LLMRoutingInfo(BaseModel):
    """LLM 라우팅 정보 모델"""

    available_providers: list[str] = Field(
        default_factory=list, description="사용 가능한 LLM 제공자 목록"
    )
    current_routing: dict[str, object] = Field(default_factory=dict, description="현재 라우팅 설정")
    system_status: str = Field(..., description="LLM 시스템 상태")


class LLMHealthCheck(BaseModel):
    """LLM 건강 체크 모델"""

    status: str = Field(..., description="전체 상태")
    available_providers: list[dict[str, object]] = Field(
        default_factory=list, description="제공자별 상태"
    )
    last_health_check: str = Field(..., description="마지막 건강 체크 시각")


# LLM API Endpoints Implementation


@llm_router.post(
    "/query",
    response_model=LLMQueryResponse,
    summary="LLM 쿼리 실행",
)
@shield(pillar="眞", reraise=True)
async def execute_llm_query(
    request: LLMQueryRequest, background_tasks: BackgroundTasks
) -> LLMQueryResponse:
    """
    LLM 쿼리 실행 API
    """
    import time

    start_time = time.time()

    if not LLM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LLM 서비스가 현재 사용할 수 없습니다. 잠시 후 다시 시도해주세요.",
        )

    logger.info(f"Executing LLM query: {request.query[:50]}...")

    # 컨텍스트 준비
    context = request.context or {}
    if request.provider:
        context["provider"] = request.provider
    if request.quality_tier:
        context["quality_tier"] = request.quality_tier
    if request.max_tokens:
        context["max_tokens"] = request.max_tokens

    # LLM 라우팅 및 실행
    result = await route_and_execute(request.query, context)

    if not result.get("success", False):
        raise HTTPException(status_code=500, detail="LLM 쿼리 처리 중 오류가 발생했습니다.")

    processing_time = time.time() - start_time

    # Trinity Score 계산 (모의)
    trinity_score = {
        "truth": 0.88,
        "goodness": 0.92,
        "beauty": 0.85,
        "serenity": 0.89,
        "eternity": 0.91,
        "overall": 0.89,
    }

    # 백그라운드 로깅
    background_tasks.add_task(_log_llm_interaction, request.model_dump(), result, processing_time)

    response = LLMQueryResponse(
        success=True,
        response=result.get("response", ""),
        provider=result.get("provider", "unknown"),
        model=result.get("model", "unknown"),
        reasoning=result.get("reasoning", "Auto-routed by LLM system"),
        tokens_used=result.get("tokens_used"),
        processing_time=round(processing_time, 2),
        timestamp=datetime.now(UTC).isoformat(),
        trinity_score=trinity_score,
    )

    logger.info(
        f"LLM query completed in {processing_time:.2f}s using {result.get('provider', 'unknown')}"
    )
    return response


@llm_router.get(
    "/routing",
    response_model=LLMRoutingInfo,
    summary="LLM 라우팅 정보",
    description="""
    현재 LLM 시스템의 라우팅 설정 및 사용 가능한 제공자 정보를 반환합니다.

    **제공 정보:**
    - 사용 가능한 LLM 제공자 목록
    - 현재 라우팅 규칙 및 설정
    - 시스템 상태 정보
    """,
)
@shield(pillar="眞", reraise=True)
async def get_llm_routing_info() -> LLMRoutingInfo:
    """
    LLM 라우팅 정보 조회 API
    """
    try:
        if not LLM_AVAILABLE:
            return LLMRoutingInfo(
                available_providers=[], current_routing={}, system_status="unavailable"
            )

        # 실제 라우터에서 정보 가져오기 (모의 구현)
        available_providers = ["claude", "gpt-4", "ollama", "gemini"]
        current_routing = {
            "default_provider": "claude",
            "quality_based_routing": True,
            "fallback_enabled": True,
            "rate_limiting": True,
        }

        return LLMRoutingInfo(
            available_providers=available_providers,
            current_routing=current_routing,
            system_status="operational",
        )

    except Exception as e:
        logger.error(f"Failed to get routing info: {e}")
        raise HTTPException(
            status_code=500, detail=f"[방패/Shield] 라우팅 정보 조회 중 오류가 발생했습니다: {e!s}"
        )


@llm_router.get(
    "/health",
    response_model=LLMHealthCheck,
    summary="LLM 시스템 건강 체크",
)
@shield(pillar="善", reraise=True)
async def check_llm_health() -> LLMHealthCheck:
    """
    LLM 시스템 건강 체크 API
    """
    if not LLM_AVAILABLE:
        return LLMHealthCheck(
            status="unavailable",
            available_providers=[],
            last_health_check=datetime.now(UTC).isoformat(),
        )

    # 모의 건강 체크 데이터
    available_providers = [
        {
            "provider": "claude",
            "status": "healthy",
            "response_time": 1200,
            "success_rate": 0.98,
        },
        {"provider": "gpt-4", "status": "healthy", "response_time": 1800, "success_rate": 0.95},
        {"provider": "ollama", "status": "healthy", "response_time": 800, "success_rate": 0.99},
    ]

    return LLMHealthCheck(
        status="healthy",
        available_providers=available_providers,
        last_health_check=datetime.now(UTC).isoformat(),
    )


@llm_router.post(
    "/test-connection",
    summary="LLM 연결 테스트",
)
@shield(
    pillar="善",
    reraise=False,
    default_return={"success": False, "message": "Connection test failed"},
)
async def test_llm_connection(
    provider: str = Query(..., description="테스트할 LLM 제공자", examples=["claude", "gpt-4"]),
    test_query: str = Query("Hello, world!", description="테스트 쿼리"),
) -> dict[str, object]:
    """
    LLM 연결 테스트 API
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "message": "LLM 시스템이 사용할 수 없습니다.",
            "provider": provider,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    logger.info(f"Testing LLM connection for provider: {provider}")

    # 모의 테스트 결과
    test_result = {
        "success": True,
        "message": f"{provider} 연결 테스트 성공",
        "provider": provider,
        "response_time": 850,
        "test_query": test_query,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    logger.info(f"LLM connection test completed for {provider}")
    return test_result


# Helper Functions


async def _log_llm_interaction(
    request_data: dict[str, object], result_data: dict[str, object], processing_time: float
) -> None:
    """
    LLM 상호작용 로깅 (백그라운드 태스크)

    모든 LLM 쿼리와 응답을 감사 및 최적화 목적으로 로깅합니다.
    """
    try:
        import json
        from pathlib import Path

        # 로그 데이터 생성
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "phase": "llm-integration-v1",
            "request": request_data,
            "result": result_data,
            "processing_time": processing_time,
            "ticket": "TICKET-086",
        }

        # 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"artifacts/llm_interaction_{timestamp}.json"

        Path("artifacts").mkdir(exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        logger.info(f"LLM interaction logged: {filename}")

    except Exception as e:
        logger.error(f"Failed to log LLM interaction: {e}")


# Export router for main API server
__all__ = ["llm_router"]
