import contextlib
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from AFO.llm_router import llm_router, route_and_execute
from AFO.utils.standard_shield import shield

# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Chat Route - LLM Router 연동 API
AICPA Core 등 프론트엔드에서 호출하는 채팅 엔드포인트
Ollama 우선 → API LLM Fallback
"""


# LLM Router instances are imported from AFO.llm_router above
with contextlib.suppress(ImportError):
    pass

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Pydantic Models ---


class ChatMessageRequest(BaseModel):
    """채팅 메시지 요청"""

    message: str = Field(..., min_length=1, max_length=10000, description="사용자 메시지")
    provider: str = Field(
        default="auto",
        description="LLM 제공자 (auto, ollama, gemini, anthropic, openai)",
    )
    quality_tier: str = Field(
        default="standard", description="품질 등급 (basic, standard, premium, ultra)"
    )
    max_tokens: int = Field(default=1024, ge=1, le=8192, description="최대 토큰 수")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="온도 설정")
    system_prompt: str | None = Field(default=None, description="시스템 프롬프트 (선택)")


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""

    success: bool
    response: str | None = None
    error: str | None = None
    routing: dict[str, str | int | float | None] | None = None
    timestamp: str


class ProviderInfo(BaseModel):
    """LLM 제공자 정보"""

    name: str
    model: str
    available: bool
    quality_tier: str
    cost_per_token: float
    latency_ms: int


class ProvidersResponse(BaseModel):
    """사용 가능한 LLM 제공자 목록"""

    providers: list[ProviderInfo]
    default_provider: str


class RoutingStatsResponse(BaseModel):
    """라우팅 통계"""

    total_requests: int
    provider_usage: dict[str, int]
    average_confidence: float
    ollama_preference_ratio: float


# --- Endpoints ---


@router.post("/message", response_model=ChatMessageResponse, summary="채팅 메시지 전송")
@shield(
    pillar="善",
    reraise=False,
    default_return=ChatMessageResponse(
        success=False, timestamp=datetime.now().isoformat(), error="Shielded chat error"
    ),
)
async def send_chat_message(request: ChatMessageRequest) -> ChatMessageResponse:
    """
    LLM Router를 통해 채팅 메시지 전송
    - Ollama 우선 사용 (무료, 빠름)
    - 불가 시 Gemini/Claude/OpenAI로 자동 Fallback
    """
    if llm_router is None or route_and_execute is None:
        raise HTTPException(status_code=503, detail="LLM Router not available")

    # 시스템 프롬프트가 있으면 메시지에 추가
    full_message = request.message
    if request.system_prompt:
        full_message = f"[System: {request.system_prompt}]\n\n{request.message}"

    # 컨텍스트 구성
    context: dict[str, str | int | float | None] = {
        "provider": request.provider,
        "quality_tier": request.quality_tier,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }

    # LLM Router 호출
    result = await route_and_execute(full_message, context)

    return ChatMessageResponse(
        success=result.get("success", False),
        response=result.get("response"),
        error=result.get("error"),
        routing=result.get("routing"),
        timestamp=datetime.now().isoformat(),
    )


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="사용 가능한 LLM 제공자 목록",
)
async def get_providers() -> ProvidersResponse:
    """현재 설정된 LLM 제공자 목록 반환"""
    if llm_router is None:
        raise HTTPException(status_code=503, detail="LLM Router not available")

    providers = []
    for provider, config in llm_router.llm_configs.items():
        providers.append(
            ProviderInfo(
                name=provider.value,
                model=config.model,
                available=True,  # 설정에 있으면 사용 가능
                quality_tier=config.quality_tier.value,
                cost_per_token=config.cost_per_token,
                latency_ms=config.latency_ms,
            )
        )

    return ProvidersResponse(
        providers=providers,
        default_provider="ollama",
    )


@router.get("/stats", response_model=RoutingStatsResponse, summary="라우팅 통계 조회")
async def get_routing_stats() -> RoutingStatsResponse:
    """LLM Router 라우팅 통계 반환"""
    if llm_router is None:
        raise HTTPException(status_code=503, detail="LLM Router not available")

    stats = llm_router.get_routing_stats()
    return RoutingStatsResponse(
        total_requests=stats.get("total_requests", 0),
        provider_usage=stats.get("provider_usage", {}),
        average_confidence=stats.get("average_confidence", 0.0),
        ollama_preference_ratio=stats.get("ollama_preference_ratio", 0.0),
    )


@router.get("/health", summary="채팅 서비스 헬스체크")
async def chat_health_check() -> dict[str, bool | str | dict | int]:
    """채팅 서비스 및 LLM Router 상태 확인"""
    if llm_router is None:
        return {
            "status": "degraded",
            "llm_router": False,
            "message": "LLM Router not initialized",
        }

    try:
        health_results = await llm_router.check_connections()
        return {
            "status": "healthy",
            "llm_router": True,
            "providers": health_results,
            "configured_count": len(llm_router.llm_configs),
        }
    except Exception as e:
        return {
            "status": "error",
            "llm_router": True,
            "error": str(e),
        }
