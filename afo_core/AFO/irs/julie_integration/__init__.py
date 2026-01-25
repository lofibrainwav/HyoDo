"""Julie CPA Integration Package.

IRS 변경 사항과 Julie CPA 시스템을 연결하는 통합 레이어.
알림 관리, 임팩트 분석 및 Evidence Bundle 연동 제공.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .alert_logic import assess_customer_impact, determine_priority, determine_severity
from .models import AlertPriority, CustomerImpact, JulieAlert


class JulieCPAIntegrator:
    """Julie CPA 통합 관리자 (Facade)."""

    def __init__(self, notification_manager=None, bundle_manager=None) -> None:
        self.notification_manager = notification_manager
        self.bundle_manager = bundle_manager
        self.alerts: dict[str, JulieAlert] = {}
        self.logger = logging.getLogger(__name__)

    async def create_and_send_alert(
        self,
        change: Any,
        parameters: dict[str, Any],
        trinity_score: Any,
        gate_result: Any,
        transaction: Any = None,
    ) -> JulieAlert | None:
        """알림을 생성하고 시스템에 전송합니다."""

        # 1. 임팩트 평가
        impact = assess_customer_impact(
            vars(change) if hasattr(change, "__dict__") else {}, parameters
        )

        # 2. 우선순위 및 심각도 결정
        priority = determine_priority(getattr(gate_result, "gate_decision", None), trinity_score)
        severity = determine_severity(priority, getattr(change, "impact", None))

        # 3. 알림 생성
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        alert = JulieAlert(
            alert_id=alert_id,
            timestamp=datetime.now().isoformat(),
            document_id=getattr(change, "document_id", "unknown"),
            document_type=getattr(change, "document_type", "IRS"),
            priority=priority,
            severity=severity,
            title=f"IRS 변경 알림: {getattr(change, 'title', 'New Regulation')}",
            message=getattr(change, "summary", "No summary available"),
            customer_impact=impact,
            transaction_id=getattr(transaction, "transaction_id", None) if transaction else None,
        )

        self.alerts[alert_id] = alert

        # 4. 외부 알림 시스템 전송
        if self.notification_manager:
            await self.notification_manager.send(alert.to_dict())

        return alert

    def get_alert_stats(self) -> dict[str, Any]:
        """알림 통계를 반환합니다."""
        total = len(self.alerts)
        unread = len([a for a in self.alerts.values() if not a.read])
        critical = len([a for a in self.alerts.values() if a.priority == AlertPriority.CRITICAL])

        return {
            "total_alerts": total,
            "unread_count": unread,
            "critical_count": critical,
            "acknowledged_count": len([a for a in self.alerts.values() if a.acknowledged]),
        }


__all__ = ["JulieCPAIntegrator", "JulieAlert", "AlertPriority", "CustomerImpact"]
