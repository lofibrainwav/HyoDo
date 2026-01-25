"""Julie Integration Models.

Julie CPA 알림 및 고객 영향 관련 데이터 모델.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AlertPriority(str, Enum):
    """알림 우선순위."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CustomerImpact:
    """고객 영향도 모델."""

    tax_years_affected: list[str]
    affected_taxpayers: str
    action_required: bool
    recommended_actions: list[str]
    deadline: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_years_affected": self.tax_years_affected,
            "affected_taxpayers": self.affected_taxpayers,
            "action_required": self.action_required,
            "recommended_actions": self.recommended_actions,
            "deadline": self.deadline,
        }


@dataclass
class JulieAlert:
    """Julie CPA 알림 모델."""

    alert_id: str
    timestamp: str
    document_id: str
    document_type: str
    priority: AlertPriority
    severity: Any  # NotificationSeverity
    title: str
    message: str
    customer_impact: CustomerImpact | None = None
    gate_decision: Any | None = None
    transaction_id: str | None = None
    bundle_id: str | None = None
    evidence_bundle_url: str | None = None
    read: bool = False
    acknowledged: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "read": self.read,
            "acknowledged": self.acknowledged,
        }
        if self.customer_impact:
            data["customer_impact"] = self.customer_impact.to_dict()
        return data
