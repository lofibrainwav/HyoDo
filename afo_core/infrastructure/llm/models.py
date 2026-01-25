from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO LLM Models (infrastructure/llm/models.py)

Enums and Data models for the Hybrid LLM Routing system.
"""


class LLMProvider(str, Enum):
    """LLM 제공자 타입 (LLM Provider Types)"""

    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI = "openai"


class QualityTier(str, Enum):
    """품질 등급 (Quality Tiers)"""

    BASIC = "basic"  # 기본 응답
    STANDARD = "standard"  # 표준 품질
    PREMIUM = "premium"  # 고품질
    ULTRA = "ultra"  # 최고 품질

    @property
    def value_rank(self) -> int:
        """Get integer rank for comparisons"""
        ranks = {
            QualityTier.BASIC: 1,
            QualityTier.STANDARD: 2,
            QualityTier.PREMIUM: 3,
            QualityTier.ULTRA: 4,
        }
        return ranks.get(self, 0)


@dataclass
class LLMConfig:
    """LLM 설정 (LLM Configuration)"""

    provider: LLMProvider
    model: str
    api_key_env: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024
    cost_per_token: float = 0.0
    latency_ms: int = 1000
    quality_tier: QualityTier = QualityTier.STANDARD
    context_window: int = 4096


@dataclass
class RoutingDecision:
    """라우팅 결정 (Routing Decision)"""

    selected_provider: LLMProvider
    selected_model: str
    reasoning: str
    confidence: float
    estimated_cost: float
    estimated_latency: int
    fallback_providers: list[LLMProvider]
