"""Result Aggregator - 결과 통합 및 Trinity Score 계산.

Strategist 결과를 통합하고 Trinity Score를 계산합니다.

AFO 철학:
- 眞善美孝永 5기둥 가중치 적용 (SSOT)
- AUTO_RUN / ASK_COMMANDER 판정
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_ASK_RISK,
    THRESHOLD_ASK_TRINITY,
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
    WEIGHTS,
)

from .models import AssessmentResult, DecisionThresholds, StrategistSummary

if TYPE_CHECKING:
    from .strategist_context import StrategistContext

logger = logging.getLogger(__name__)


class ResultAggregator:
    """Strategist 결과 통합 및 Trinity Score 계산.

    SSOT 가중치를 사용하여 Trinity Score를 계산하고,
    AUTO_RUN / ASK_COMMANDER 판정을 수행합니다.

    Formula:
        Trinity = 0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永
        (SERENITY와 ETERNITY는 별도 노드에서 제공)

    Thresholds:
        - AUTO_RUN: Trinity >= 90 AND Risk <= 10
        - ASK_COMMANDER: Trinity >= 75 AND Risk <= 25
        - BLOCK: Otherwise
    """

    def calculate_trinity_score(
        self,
        results: dict[str, StrategistContext],
        serenity_score: float = 0.8,
        eternity_score: float = 0.8,
    ) -> tuple[float, dict[str, float]]:
        """Trinity Score 계산.

        Args:
            results: Strategist별 완료된 컨텍스트
            serenity_score: 孝 점수 (별도 노드에서 제공, 기본 0.8)
            eternity_score: 永 점수 (별도 노드에서 제공, 기본 0.8)

        Returns:
            (trinity_score, pillar_scores) 튜플
            - trinity_score: 0-100 범위의 최종 점수
            - pillar_scores: 각 기둥별 0-1 점수
        """
        # 각 Strategist 결과에서 점수 추출
        pillar_scores = {
            "truth": self._extract_score(results, "truth"),
            "goodness": self._extract_score(results, "goodness"),
            "beauty": self._extract_score(results, "beauty"),
            "serenity": serenity_score,
            "eternity": eternity_score,
        }

        # SSOT 가중치로 Trinity Score 계산
        trinity_raw = sum(pillar_scores[pillar] * WEIGHTS[pillar] for pillar in pillar_scores)

        # 0-100 스케일로 변환
        trinity_score = round(trinity_raw * 100, 2)

        logger.debug(
            f"Trinity Score calculated: {trinity_score:.2f} "
            f"(T:{pillar_scores['truth']:.2f} G:{pillar_scores['goodness']:.2f} "
            f"B:{pillar_scores['beauty']:.2f} S:{pillar_scores['serenity']:.2f} "
            f"E:{pillar_scores['eternity']:.2f})"
        )

        return trinity_score, pillar_scores

    def calculate_risk_score(self, pillar_scores: dict[str, float]) -> float:
        """Risk Score 계산.

        Risk는 Goodness(善)의 반대 개념으로 계산합니다.
        Risk = (1.0 - Goodness) × 100

        Args:
            pillar_scores: 각 기둥별 점수

        Returns:
            0-100 범위의 Risk Score
        """
        goodness = pillar_scores.get("goodness", 0.5)
        risk_score = round((1.0 - goodness) * 100, 2)
        return risk_score

    def make_decision(
        self,
        trinity_score: float,
        risk_score: float,
        pillar_scores: dict[str, float],
    ) -> dict[str, Any]:
        """DecisionResult 생성.

        Trinity Score와 Risk Score를 기반으로 판정합니다.

        Args:
            trinity_score: 0-100 범위의 Trinity Score
            risk_score: 0-100 범위의 Risk Score
            pillar_scores: 각 기둥별 점수

        Returns:
            DecisionResult 딕셔너리
        """
        # 판정 로직
        if trinity_score >= THRESHOLD_AUTO_RUN_SCORE and risk_score <= THRESHOLD_AUTO_RUN_RISK:
            decision = "AUTO_RUN"
            confidence = min(trinity_score / 100, 0.99)
        elif trinity_score >= THRESHOLD_ASK_TRINITY and risk_score <= THRESHOLD_ASK_RISK:
            decision = "ASK_COMMANDER"
            confidence = trinity_score / 100 * 0.8
        else:
            decision = "BLOCK"
            confidence = 1.0 - (trinity_score / 100)

        result = {
            "decision": decision,
            "trinity_score": trinity_score,
            "risk_score": risk_score,
            "confidence": round(confidence, 3),
            "pillar_scores": {k: round(v, 3) for k, v in pillar_scores.items()},
            "thresholds": DecisionThresholds(
                auto_run_trinity=THRESHOLD_AUTO_RUN_SCORE,
                auto_run_risk=THRESHOLD_AUTO_RUN_RISK,
                ask_trinity=THRESHOLD_ASK_TRINITY,
                ask_risk=THRESHOLD_ASK_RISK,
            ),
        }

        logger.info(f"Decision: {decision} (Trinity: {trinity_score:.2f}, Risk: {risk_score:.2f})")

        return result

    def aggregate_results(
        self,
        results: dict[str, StrategistContext],
        serenity_score: float = 0.8,
        eternity_score: float = 0.8,
    ) -> AssessmentResult:
        """전체 결과 통합.

        Strategist 결과를 받아 Trinity Score, Risk Score를 계산하고
        최종 DecisionResult를 생성합니다.

        Args:
            results: Strategist별 완료된 컨텍스트
            serenity_score: 孝 점수
            eternity_score: 永 점수

        Returns:
            통합된 결과 모델
        """
        trinity_score, pillar_scores = self.calculate_trinity_score(
            results, serenity_score, eternity_score
        )
        risk_score = self.calculate_risk_score(pillar_scores)
        decision = self.make_decision(trinity_score, risk_score, pillar_scores)

        # 개별 Strategist 결과 요약
        strategist_summaries = {}
        for pillar, ctx in results.items():
            strategist_summaries[pillar] = StrategistSummary(
                score=ctx.score,
                reasoning=ctx.reasoning[:200] if ctx.reasoning else "",
                issues_count=len(ctx.issues),
                has_errors=ctx.has_errors,
                duration_ms=ctx.duration_ms,
            )

        return AssessmentResult(
            decision=decision["decision"],
            trinity_score=decision["trinity_score"],
            risk_score=decision["risk_score"],
            confidence=decision["confidence"],
            pillar_scores=decision["pillar_scores"],
            thresholds=decision["thresholds"],
            strategist_results=strategist_summaries,
        )

    def _extract_score(
        self,
        results: dict[str, StrategistContext],
        pillar: str,
    ) -> float:
        """결과에서 점수 추출.

        Args:
            results: Strategist 결과
            pillar: 기둥 이름

        Returns:
            점수 (기본값 0.5)
        """
        ctx = results.get(pillar.lower())
        if ctx and hasattr(ctx, "score"):
            return ctx.score
        return 0.5  # 기본값
