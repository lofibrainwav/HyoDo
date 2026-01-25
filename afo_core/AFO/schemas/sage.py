# Trinity Score: 90.0 (Established by Chancellor)
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import Field

from AFO.schemas.base import BaseSchema


class SageType(str, Enum):
    """Type of Sage (MoE Expert)

    3 Sages (영덕 Ollama Local MoE):
    - SAMAHWI (사마휘): Qwen2.5-Coder-32B - Python backend (眞/善)
    - JWAJA (좌자): DeepSeek-R1 - Frontend (美/孝)
    - HWATA (화타): Qwen3-VL - UX copywriter (孝/美)

    Korean Scholars:
    - JEONG_YAK_YONG (정약용): 실학자
    - RYU_SEONG_RYONG (류성룡): 징비록
    - HEO_JUN (허준): 동의보감
    """

    # 3 Sages (영덕 Ollama Local MoE)
    SAMAHWI = "samahwi"  # 사마휘 - Qwen2.5-Coder-32B (眞/善)
    JWAJA = "jwaja"  # 좌자 - DeepSeek-R1 (美/孝)
    HWATA = "hwata"  # 화타 - Qwen3-VL Vision/UX (孝/美)

    # Korean Scholars
    JEONG_YAK_YONG = "jeong_yak_yong"
    RYU_SEONG_RYONG = "ryu_seong_ryong"
    HEO_JUN = "heo_jun"


class SageRequest(BaseSchema):
    """
    Request to a Yeongdeok Sage
    Validation ensures Truth (Correct Expert) & Goodness (Safe Prompt)
    """

    sage: SageType = Field(..., description="Target Sage (Expert)")
    prompt: str = Field(..., min_length=1, description="User query / prompt")
    system_context: str | None = Field(None, description="Optional override system prompt")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Creativity control")


class SageResponse(BaseSchema):
    """
    Response from a Yeongdeok Sage
    Validation ensures strict output format
    """

    sage: SageType = Field(..., description="Sage who responded")
    content: str = Field(..., description="Generated content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Time of generation"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Execution metadata (latency, tokens)"
    )
    is_fallback: bool = Field(default=False, description="Whether fallback mechanism was used")
