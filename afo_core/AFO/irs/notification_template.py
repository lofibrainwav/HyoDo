"""
Notification Template - 알림 템플릿 및 포맷

美 (Zhou Yu): 단순함/일관성
- 알림 템플릿 설계
- 단순한 API 포맷
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NotificationSeverity:
    """알림 심각도"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NotificationChannel:
    """알림 채널"""

    EMAIL = "email"
    SMS = "sms"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SYSTEM = "system"


@dataclass
class NotificationTemplate:
    """알림 템플릿"""

    template_id: str
    name: str
    severity: NotificationSeverity
    channel: NotificationChannel
    subject_template: str
    body_template: str
    metadata_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "severity": self.severity,
            "channel": self.channel,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "metadata_fields": self.metadata_fields,
        }


class NotificationManager:
    """알림 관리자"""

    TEMPLATES = {
        "irs_change_critical": NotificationTemplate(
            template_id="irs_change_critical",
            name="IRS Critical Change",
            severity=NotificationSeverity.CRITICAL,
            channel=NotificationChannel.EMAIL,
            subject_template="🚨 IRS Critical Changes Detected: {document_name}",
            body_template="**Impact Areas**: {impact_areas}\n\n**Severity**: Critical\n**Detected At**: {detected_at}\n\n**Evidence Bundle ID**: {evidence_bundle_id}\n\n**Summary**: {summary}",
            metadata_fields=[
                "document_name",
                "impact_areas",
                "detected_at",
                "evidence_bundle_id",
                "summary",
            ],
        ),
        "irs_change_high": NotificationTemplate(
            template_id="irs_change_high",
            name="IRS High Priority Change",
            severity=NotificationSeverity.HIGH,
            channel=NotificationChannel.EMAIL,
            subject_template="⚠️  IRS High Priority Changes: {document_name}",
            body_template="**Impact Areas**: {impact_areas}\n\n**Severity**: High\n**Detected At**: {detected_at}\n\n**Evidence Bundle ID**: {evidence_bundle_id}\n\n**Summary**: {summary}",
            metadata_fields=[
                "document_name",
                "impact_areas",
                "evidence_bundle_id",
                "summary",
            ],
        ),
        "irs_change_medium": NotificationTemplate(
            template_id="irs_change_medium",
            name="IRS Medium Priority Change",
            severity=NotificationSeverity.MEDIUM,
            channel=NotificationChannel.EMAIL,
            subject_template="📋 IRS Changes: {document_name}",
            body_template="**Impact Areas**: {impact_areas}\n\n**Severity**: Medium\n**Detected At**: {detected_at}\n\n**Evidence Bundle ID**: {evidence_bundle_id}\n\n**Summary**: {summary}",
            metadata_fields=[
                "document_name",
                "impact_areas",
                "evidence_bundle_id",
                "summary",
            ],
        ),
        "irs_change_low": NotificationTemplate(
            template_id="irs_change_low",
            name="IRS Low Priority Change",
            severity=NotificationSeverity.INFO,
            channel=NotificationChannel.DISCORD,
            subject_template="📌 IRS Changes: {document_name}",
            body_template="**Impact Areas**: {impact_areas}\n\n**Severity**: Info\n**Detected At**: {detected_at}\n\n**Evidence Bundle ID**: {evidence_bundle_id}\n\n**Summary**: {summary}",
            metadata_fields=[
                "document_name",
                "impact_areas",
                "evidence_bundle_id",
                "summary",
            ],
        ),
        "monitoring_started": NotificationTemplate(
            template_id="monitoring_started",
            name="Monitoring Started",
            severity=NotificationSeverity.INFO,
            channel=NotificationChannel.SYSTEM,
            subject_template="IRS Monitor Started",
            body_template="**Monitor Agent**: IRS Monitor Agent {agent_id}\n**Status**: Running\n**Interval**: {interval_hours} hours\n**Started At**: {timestamp}",
            metadata_fields=[
                "agent_id",
                "interval_hours",
                "timestamp",
            ],
        ),
        "monitoring_error": NotificationTemplate(
            template_id="monitoring_error",
            name="Monitoring Error",
            severity=NotificationSeverity.ERROR,
            channel=NotificationChannel.SYSTEM,
            subject_template="❌ IRS Monitor Error",
            body_template="**Monitor Agent**: IRS Monitor Agent {agent_id}\n**Error**: {error_type}\n**Message**: {error_message}\n**Occurred At**: {timestamp}\n**Traceback**: {traceback[:200]}",
            metadata_fields=[
                "agent_id",
                "error_type",
                "error_message",
                "timestamp",
                "traceback",
            ],
        ),
    }

    def __init__(self) -> None:
        """알림 관리자 초기화"""
        logger.info("알림 관리자 초기화 완료")

    def get_template(self, template_id: str) -> NotificationTemplate | None:
        """
        템플릿 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            NotificationTemplate 또는 None
        """
        return self.TEMPLATES.get(template_id)

    def render_notification(
        self,
        template_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        알림 렌더링

        Args:
            template_id: 템플릿 ID
            context: 렌더링 컨텍스트

        Returns:
            렌더링된 알림 딕셔너리
        """
        template = self.get_template(template_id)

        if template is None:
            logger.error(f"템플릿을 찾을 수 없음: {template_id}")
            return {
                "template_id": template_id,
                "rendered_at": datetime.now().isoformat(),
                "status": "error",
                "error": "Template not found",
            }

        # 메타데이터 준비
        metadata = {}

        # 필드 매핑
        for field_name in template.metadata_fields:
            value = context.get(field_name, "")
            if value:
                metadata[field_name] = str(value)
            else:
                metadata[field_name] = "N/A"

        # 템플릿 변수 치환
        subject = template.subject_template.format(**context)
        body = template.body_template.format(**context, **metadata)

        rendered = {
            "template_id": template.template_id,
            "template": template.to_dict(),
            "rendered_at": datetime.now().isoformat(),
            "status": "rendered",
            "subject": subject,
            "body": body,
            "metadata": metadata,
        }

        logger.debug(
            f"알림 레더링: template_id={template_id}, "
            f"severity={template.severity}, "
            f"channel={template.channel}"
        )

        return rendered

    def send_notification(
        self,
        notification: dict[str, Any],
    ) -> dict[str, Any]:
        """
        알림 발송 (stub)

        Args:
            notification: 렌더링된 알림 딕셔너리

        Returns:
            발송 결과
        """
        logger.info(
            f"알림 발송: channel={notification['channel']}, template={notification['template_id']}"
        )

        return {
            "sent_at": datetime.now().isoformat(),
            "channel": notification["channel"],
            "template_id": notification["template_id"],
            "status": "queued",
            "notification": notification,
        }

    def batch_render_notifications(
        self,
        template_id: str,
        contexts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        배치 알림 렌더링

        Args:
            template_id: 템플릿 ID
            contexts: 렌더링 컨텍스트 리스트

        Returns:
            렌더링된 알림 리스트
        """
        return [self.render_notification(template_id, context) for context in contexts]

    def render_irs_change_notification(
        self,
        severity: str,
        document_name: str,
        impact_areas: list[str],
        detected_at: str,
        summary: str,
        evidence_bundle_id: str,
    ) -> dict[str, Any]:
        """
        IRS 변경 알림 레더링 (편의 함수)

        Args:
            severity: 심각도 (critical, high, medium, low)
            document_name: 문서 이름
            impact_areas: 영향 영역
            detected_at: 감지 시각
            summary: 요약
            evidence_bundle_id: Evidence Bundle ID

        Returns:
            렌더링된 알림 딕셔너리
        """
        if severity == "critical":
            template_id = "irs_change_critical"
        elif severity == "high":
            template_id = "irs_change_high"
        elif severity == "medium":
            template_id = "irs_change_medium"
        else:
            template_id = "irs_change_low"

        context = {
            "document_name": document_name,
            "impact_areas": ", ".join(impact_areas),
            "detected_at": detected_at,
            "evidence_bundle_id": evidence_bundle_id,
            "summary": summary,
        }

        return self.render_notification(template_id, context)

    def get_available_templates(self) -> dict[str, NotificationTemplate]:
        """사용 가능한 템플릿 목록 반환"""
        return self.TEMPLATES


# Convenience Functions
def get_template(template_id: str) -> NotificationTemplate | None:
    """템플릿 조회 (편의 함수)"""
    manager = NotificationManager()
    return manager.get_template(template_id)


def render_irs_change_notification(
    severity: str,
    document_name: str,
    impact_areas: list[str],
    detected_at: str,
    summary: str,
    evidence_bundle_id: str,
) -> dict[str, Any]:
    """IRS 변경 알림 레더링 (편의 함수)"""
    manager = NotificationManager()
    return manager.render_irs_change_notification(
        severity,
        document_name,
        impact_areas,
        detected_at,
        summary,
        evidence_bundle_id,
    )


__all__ = [
    "NotificationSeverity",
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationManager",
    "get_template",
    "render_irs_change_notification",
]
