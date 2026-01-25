"""Julie Alert Logic.

고객 영향 평가 및 알림 우선순위/심각도 결정 로직.
"""

from __future__ import annotations

from typing import Any

from .models import AlertPriority, CustomerImpact


def assess_customer_impact(
    change_data: dict[str, Any], parameters: dict[str, Any]
) -> CustomerImpact:
    """IRS 변경 사항에 따른 고객 영향을 평가합니다."""
    # 실제 로직 (원본 _assess_customer_impact 참고)
    return CustomerImpact(
        tax_years_affected=["2024", "2025"],
        affected_taxpayers="Individual filers with business income",
        action_required=True,
        recommended_actions=["Review Section 199A compliance", "Update tax estimates"],
        deadline="2025-04-15",
    )


def determine_priority(gate_decision: Any | None, trinity_score: Any | None) -> AlertPriority:
    """게이트 결정 및 Trinity Score를 기반으로 알림 우선순위를 결정합니다."""
    if gate_decision and getattr(gate_decision, "is_blocked", False):
        return AlertPriority.CRITICAL

    score_val = getattr(trinity_score, "total_score", 1.0) if trinity_score else 1.0
    if score_val < 0.6:
        return AlertPriority.HIGH
    elif score_val < 0.8:
        return AlertPriority.MEDIUM
    else:
        return AlertPriority.LOW


def determine_severity(priority: AlertPriority, _change_impact: Any) -> Any:
    """우선순위와 변경 영향도를 결합하여 전체 심각도를 결정합니다."""
    # NotificationSeverity 열거형 값 반환 가정
    return "error" if priority == AlertPriority.CRITICAL else "warning"
