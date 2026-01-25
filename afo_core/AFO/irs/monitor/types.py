from typing import Any


class IRSChangeEvent:
    """IRS 변경 이벤트 데이터 클래스"""

    def __init__(
        self,
        event_id: str,
        change_type: str,
        source_url: str,
        title: str,
        content_preview: str,
        detected_at: str,
        severity: str = "medium",
        affected_areas: list[str] | None = None,
        action_required: bool = True,
    ):
        self.event_id = event_id
        self.change_type = (
            change_type  # 'publication_update', 'revenue_procedure', 'notice', 'tax_code_change'
        )
        self.source_url = source_url
        self.title = title
        self.content_preview = content_preview
        self.detected_at = detected_at
        self.severity = severity  # 'low', 'medium', 'high', 'critical'
        self.affected_areas = affected_areas or []
        self.action_required = action_required

    def to_dict(self) -> dict[str, Any]:
        """이벤트 데이터를 딕셔너리로 변환"""
        return {
            "event_id": self.event_id,
            "change_type": self.change_type,
            "source_url": self.source_url,
            "title": self.title,
            "content_preview": self.content_preview,
            "detected_at": self.detected_at,
            "severity": self.severity,
            "affected_areas": self.affected_areas,
            "action_required": self.action_required,
        }
