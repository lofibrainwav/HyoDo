"""
Trinity Score Gate - Trinity Score 기반 검증 게이트

眞 (장영실 - Jang Yeong-sil): 기술적 확실성/타입 안전성
善 (이순신 - Yi Sun-sin): 보안/리스크/PII 보호
美 (신사임당 - Shin Saimdang): 단순함/일관성/구조화

5기둥 Trinity Score 검증 시스템
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .evidence_bundle_extended import EvidenceBundleExtended, TrinityScore

logger = logging.getLogger(__name__)


class GateDecision(Enum):
    """게이트 결정"""

    AUTO_RUN = "auto_run"  # 자동 실행
    ASK_COMMANDER = "ask_commander"  # 사령관 승인 필요
    BLOCK = "block"  # 차단


@dataclass
class GateResult:
    """게이트 결과"""

    decision: GateDecision
    trinity_score: float
    risk_score: float
    reason: str
    evidence_bundle: EvidenceBundleExtended | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "decision": self.decision.value,
            "trinity_score": self.trinity_score,
            "risk_score": self.risk_score,
            "reason": self.reason,
            "evidence_bundle": (self.evidence_bundle.to_dict() if self.evidence_bundle else None),
            "timestamp": self.timestamp,
        }


class TrinityGate:
    """
    Trinity Score 기반 검증 게이트

    Decision Matrix:
    | Trinity Score | Risk Score | Decision      |
    | ------------- | ---------- | ------------- |
    | ≥ 90          | ≤ 10       | AUTO_RUN      |
    | 70-89         | ≤ 10       | ASK_COMMANDER |
    | < 70          | any        | BLOCK         |
    """

    def __init__(
        self,
        min_auto_run_score: float = 0.90,
        min_ask_score: float = 0.70,
        max_risk_score: float = 0.10,
    ):
        self.min_auto_run_score = min_auto_run_score
        self.min_ask_score = min_ask_score
        self.max_risk_score = max_risk_score

    def evaluate(
        self,
        trinity_score: TrinityScore | float,
        risk_score: float,
        evidence_bundle: EvidenceBundleExtended | None = None,
    ) -> GateResult:
        """
        Trinity Score 기반 검증

        Args:
            trinity_score: Trinity Score 또는 전체 점수
            risk_score: 리스크 점수 (0-1)
            evidence_bundle: Evidence Bundle

        Returns:
            게이트 결과
        """
        # Trinity Score 추출
        if isinstance(trinity_score, TrinityScore):
            total_score = trinity_score.total
        else:
            total_score = trinity_score

        # Risk Score 계산 (善)
        # Goodness가 낮을수록 Risk가 높음
        calculated_risk_score = self._calculate_risk_score(trinity_score, risk_score)

        # 결정 로직
        decision, reason = self._make_decision(total_score, calculated_risk_score)

        logger.info(f"Trinity Gate: {decision.value}")
        logger.info(f"  Trinity Score: {total_score:.2%}")
        logger.info(f"  Risk Score: {calculated_risk_score:.2%}")
        logger.info(f"  Reason: {reason}")

        return GateResult(
            decision=decision,
            trinity_score=total_score,
            risk_score=calculated_risk_score,
            reason=reason,
            evidence_bundle=evidence_bundle,
        )

    def _calculate_risk_score(
        self, trinity_score: TrinityScore | float, manual_risk_score: float
    ) -> float:
        """
        리스크 점수 계산

        Args:
            trinity_score: Trinity Score
            manual_risk_score: 수동 리스크 점수

        Returns:
            최종 리스크 점수
        """
        if isinstance(trinity_score, TrinityScore):
            # 善 (Goodness)가 낮을수록 리스크 높음
            goodness_risk = 1.0 - trinity_score.goodness
            # 최종 리스크는 수동 리스크와 Goodness 리스크의 최댓값
            return max(manual_risk_score, goodness_risk)
        else:
            return manual_risk_score

    def _make_decision(self, trinity_score: float, risk_score: float) -> tuple[GateDecision, str]:
        """
        결정 로직

        Args:
            trinity_score: Trinity Score
            risk_score: 리스크 점수

        Returns:
            (결정, 사유)
        """
        # BLOCK: Trinity Score 부족
        if trinity_score < self.min_ask_score:
            return (
                GateDecision.BLOCK,
                f"Trinity Score 부족 ({trinity_score:.2%} < {self.min_ask_score:.2%})",
            )

        # BLOCK: Risk Score 초과
        if risk_score > self.max_risk_score:
            return (
                GateDecision.BLOCK,
                f"Risk Score 초과 ({risk_score:.2%} > {self.max_risk_score:.2%})",
            )

        # AUTO_RUN: 높은 Trinity Score + 낮은 Risk
        if trinity_score >= self.min_auto_run_score and risk_score <= self.max_risk_score:
            return (
                GateDecision.AUTO_RUN,
                f"자동 실행 가능 (Trinity Score {trinity_score:.2%}, Risk Score {risk_score:.2%})",
            )

        # ASK_COMMANDER: 중간 Trinity Score + 낮은 Risk
        return (
            GateDecision.ASK_COMMANDER,
            f"사령관 승인 필요 (Trinity Score {trinity_score:.2%}, Risk Score {risk_score:.2%})",
        )

    def validate_pillars(self, trinity_score: TrinityScore) -> dict[str, bool]:
        """
        개별 기둥 검증

        Args:
            trinity_score: Trinity Score

        Returns:
            기둥별 검증 결과
        """
        return {
            "眞 (Truth)": trinity_score.truth >= 0.90,
            "善 (Goodness)": trinity_score.goodness >= 0.85,
            "美 (Beauty)": trinity_score.beauty >= 0.80,
            "孝 (Serenity)": trinity_score.serenity >= 0.80,
            "永 (Eternity)": trinity_score.eternity >= 0.90,
        }

    def get_pillar_details(self, trinity_score: TrinityScore) -> dict[str, Any]:
        """
        기둥별 상세 정보

        Args:
            trinity_score: Trinity Score

        Returns:
            기둥별 상세 정보
        """
        return {
            "眞 (Truth)": {
                "score": trinity_score.truth,
                "weight": 0.35,
                "description": "기술적 확실성/타입 안전성",
                "status": "PASS" if trinity_score.truth >= 0.90 else "FAIL",
            },
            "善 (Goodness)": {
                "score": trinity_score.goodness,
                "weight": 0.35,
                "description": "보안/리스크/PII 보호",
                "status": "PASS" if trinity_score.goodness >= 0.85 else "FAIL",
            },
            "美 (Beauty)": {
                "score": trinity_score.beauty,
                "weight": 0.20,
                "description": "단순함/일관성/구조화",
                "status": "PASS" if trinity_score.beauty >= 0.80 else "FAIL",
            },
            "孝 (Serenity)": {
                "score": trinity_score.serenity,
                "weight": 0.08,
                "description": "평온 수호/운영 마찰 제거",
                "status": "PASS" if trinity_score.serenity >= 0.80 else "FAIL",
            },
            "永 (Eternity)": {
                "score": trinity_score.eternity,
                "weight": 0.02,
                "description": "영속성/결정 기록",
                "status": "PASS" if trinity_score.eternity >= 0.90 else "FAIL",
            },
        }

    def explain_decision(self, gate_result: GateResult) -> str:
        """
        결정 설명

        Args:
            gate_result: 게이트 결과

        Returns:
            설명 문자열
        """
        if gate_result.evidence_bundle:
            trinity_score = gate_result.evidence_bundle.trinity_score
            pillar_details = self.get_pillar_details(trinity_score)

            explanation = f"""
# Trinity Gate 결정

## 결정: {gate_result.decision.value.upper()}

## 전체 점수
- **Trinity Score**: {gate_result.trinity_score:.2%}
- **Risk Score**: {gate_result.risk_score:.2%}

## 기둥별 점수
"""

            for pillar, details in pillar_details.items():
                status_emoji = "✅" if details["status"] == "PASS" else "❌"
                explanation += f"- {status_emoji} **{pillar}**: {details['score']:.2%} (가중치: {details['weight']:.0%}) - {details['description']}\n"

            explanation += f"\n## 사유\n{gate_result.reason}\n"
            explanation += f"\n## 타임스탬프\n{gate_result.timestamp}\n"

            return explanation

        return f"# Trinity Gate 결정\n\n## 결정: {gate_result.decision.value.upper()}\n\n## 사유\n{gate_result.reason}\n\n## 타임스탬프\n{gate_result.timestamp}\n"
