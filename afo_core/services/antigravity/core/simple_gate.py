# Trinity Score: 90.0 (Established by Chancellor)
"""
Simple Antigravity Core - 불변 품질 게이트
AGENTS.md Rule #1 준수: Trinity Score 기반 단순 품질 판정

외과 수술 전 CT 판독처럼, 감정 없이 사실만 판정합니다.
"""

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
)
from AFO.observability.verdict_event import Decision

# AGENTS.md Rule #1: AUTO_RUN 조건 (SSOT re-export)
AUTO_RUN_TRINITY_THRESHOLD = int(THRESHOLD_AUTO_RUN_SCORE)
AUTO_RUN_RISK_THRESHOLD = int(THRESHOLD_AUTO_RUN_RISK)


def evaluate_gate(trinity_score: float, risk_score: float) -> Decision:
    """
    단순 품질 게이트 평가 (AGENTS.md Rule #1)

    Args:
        trinity_score: 0-100 사이의 Trinity Score
        risk_score: 0-100 사이의 Risk Score

    Returns:
        품질 게이트 결정

    Rules:
        AUTO_RUN: Trinity >= 90 AND Risk <= 10
        ASK_COMMANDER: 위 조건 미충족
        BLOCK: 추가 판정 필요 시 (현재는 사용하지 않음)
    """
    # 입력 검증
    if not (0 <= trinity_score <= 100):
        raise ValueError(f"Trinity Score는 0-100 사이여야 함: {trinity_score}")
    if not (0 <= risk_score <= 100):
        raise ValueError(f"Risk Score는 0-100 사이여야 함: {risk_score}")

    # AGENTS.md Rule #1 적용
    if trinity_score >= AUTO_RUN_TRINITY_THRESHOLD and risk_score <= AUTO_RUN_RISK_THRESHOLD:
        return Decision.AUTO_RUN

    return Decision.ASK_COMMANDER


def is_auto_run_eligible(trinity_score: float, risk_score: float) -> bool:
    """
    AUTO_RUN 자격 여부 확인 (편의 함수)

    Args:
        trinity_score: Trinity Score (0-100)
        risk_score: Risk Score (0-100)

    Returns:
        AUTO_RUN 가능 여부
    """
    return evaluate_gate(trinity_score, risk_score) == Decision.AUTO_RUN
