# Trinity Score: 94.0 (善 - Cost Optimization & Resource Management)
"""Cost-Aware Model Router for Chancellor V3.

작업 복잡도에 따라 최적의 모델을 선택하여 API 비용을 절감합니다.

AFO 철학:
- 善 (Goodness): 리소스 효율적 사용
- 孝 (Serenity): 사용자 비용 부담 최소화
- 永 (Eternity): 지속 가능한 운영
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from .models import CostEstimate, CostTier, ModelConfig

logger = logging.getLogger(__name__)


# 기본 모델 설정
DEFAULT_MODELS: dict[CostTier, ModelConfig] = {
    CostTier.FREE: ModelConfig(
        model_id=os.getenv("AFO_FREE_MODEL", "qwen3:8b"),
        provider="ollama",
        cost_tier=CostTier.FREE,
        max_tokens=8192,
        quality_score=0.70,
        cost_per_1k_tokens=0.0,
    ),
    CostTier.CHEAP: ModelConfig(
        model_id=os.getenv("AFO_CHEAP_MODEL", "claude-haiku-4-5-20251001"),
        provider="anthropic",
        cost_tier=CostTier.CHEAP,
        max_tokens=4096,
        quality_score=0.85,
        cost_per_1k_tokens=0.00025,
    ),
    CostTier.EXPENSIVE: ModelConfig(
        model_id=os.getenv("AFO_EXPENSIVE_MODEL", "claude-opus-4-5-20251101"),
        provider="anthropic",
        cost_tier=CostTier.EXPENSIVE,
        max_tokens=8192,
        quality_score=0.98,
        cost_per_1k_tokens=0.015,
    ),
}


@dataclass
class CostAwareRouter:
    """비용 인식 모델 라우터.

    작업 복잡도를 분석하여 최적의 비용/품질 모델을 선택합니다.

    Usage:
        router = CostAwareRouter()
        tier = router.estimate_complexity(command, plan)
        model = router.get_model(tier)

        # 또는 한 번에
        model = router.select_model(command, plan)
    """

    models: dict[CostTier, ModelConfig] = field(default_factory=lambda: DEFAULT_MODELS.copy())
    force_tier: CostTier | None = None  # 강제 티어 지정 (테스트용)

    # 복잡도 판단 키워드
    HIGH_COMPLEXITY_KEYWORDS: list[str] = field(
        default_factory=lambda: [
            r"prod(uction)?",
            r"deploy",
            r"delete",
            r"drop",
            r"auth(entication)?",
            r"secret",
            r"password",
            r"credential",
            r"migration",
            r"refactor",
            r"architect",
        ]
    )

    MEDIUM_COMPLEXITY_KEYWORDS: list[str] = field(
        default_factory=lambda: [
            r"implement",
            r"create",
            r"add",
            r"update",
            r"modify",
            r"test",
            r"debug",
            r"fix",
        ]
    )

    LOW_COMPLEXITY_KEYWORDS: list[str] = field(
        default_factory=lambda: [
            r"read",
            r"list",
            r"show",
            r"explain",
            r"search",
            r"find",
            r"help",
            r"doc(s)?",
        ]
    )

    def estimate_complexity(self, command: str, plan: dict[str, Any] | None = None) -> CostTier:
        """작업 복잡도 추정.

        Args:
            command: 사용자 명령어
            plan: 실행 계획 (선택)

        Returns:
            추정된 비용 티어
        """
        if self.force_tier:
            return self.force_tier

        complexity_score = 0
        command_lower = command.lower()
        plan = plan or {}

        # 1. 명령어 길이 기반 점수
        cmd_len = len(command)
        if cmd_len > 500:
            complexity_score += 3
        elif cmd_len > 200:
            complexity_score += 2
        elif cmd_len > 100:
            complexity_score += 1

        # 2. 고복잡도 키워드 체크
        for pattern in self.HIGH_COMPLEXITY_KEYWORDS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                complexity_score += 3
                logger.debug(f"High complexity keyword matched: {pattern}")

        # 3. 중복잡도 키워드 체크
        for pattern in self.MEDIUM_COMPLEXITY_KEYWORDS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                complexity_score += 1

        # 4. 저복잡도 키워드 체크 (감점)
        for pattern in self.LOW_COMPLEXITY_KEYWORDS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                complexity_score -= 1

        # 5. Plan 복잡도
        steps = plan.get("steps", [])
        if len(steps) > 5:
            complexity_score += 2
        elif len(steps) > 3:
            complexity_score += 1

        # 6. 특수 플래그 체크
        if plan.get("requires_approval"):
            complexity_score += 2
        if plan.get("dry_run"):
            complexity_score -= 1  # DRY_RUN은 덜 위험

        # 티어 결정
        if complexity_score >= 5:
            tier = CostTier.EXPENSIVE
        elif complexity_score >= 2:
            tier = CostTier.CHEAP
        else:
            tier = CostTier.FREE

        logger.info(f"[CostAwareRouter] Complexity score: {complexity_score} -> Tier: {tier.value}")
        return tier

    def get_model(self, tier: CostTier) -> ModelConfig:
        """티어에 해당하는 모델 반환.

        Args:
            tier: 비용 티어

        Returns:
            모델 설정
        """
        return self.models.get(tier, self.models[CostTier.CHEAP])

    def select_model(self, command: str, plan: dict[str, Any] | None = None) -> ModelConfig:
        """명령어/계획 기반 최적 모델 선택.

        Args:
            command: 사용자 명령어
            plan: 실행 계획 (선택)

        Returns:
            선택된 모델 설정
        """
        tier = self.estimate_complexity(command, plan)
        return self.get_model(tier)

    def get_provider_config(
        self, command: str, plan: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """LLM Router용 provider 설정 반환.

        Args:
            command: 사용자 명령어
            plan: 실행 계획

        Returns:
            LLM Router context에 전달할 설정
        """
        model = self.select_model(command, plan)
        return {
            "provider": model.provider,
            "model": model.model_id,
            "quality_tier": model.cost_tier.value,
            "max_tokens": model.max_tokens,
        }

    def estimate_cost(
        self, command: str, plan: dict[str, Any] | None = None, estimated_tokens: int = 2000
    ) -> CostEstimate:
        """예상 비용 계산.

        Args:
            command: 사용자 명령어
            plan: 실행 계획
            estimated_tokens: 예상 토큰 수

        Returns:
            비용 추정 정보
        """
        model = self.select_model(command, plan)
        estimated_cost = (estimated_tokens / 1000) * model.cost_per_1k_tokens

        return CostEstimate(
            tier=model.cost_tier.value,
            model=model.model_id,
            estimated_tokens=estimated_tokens,
            estimated_cost_usd=round(estimated_cost, 6),
            quality_score=model.quality_score,
        )


# 싱글톤 인스턴스
_router: CostAwareRouter | None = None


def get_cost_aware_router() -> CostAwareRouter:
    """CostAwareRouter 싱글톤 반환."""
    global _router
    if _router is None:
        _router = CostAwareRouter()
    return _router
