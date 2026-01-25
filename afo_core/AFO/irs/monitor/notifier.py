import logging

from AFO.irs.monitor.types import IRSChangeEvent
from AFO.irs_source_registry import irs_source_registry
from AFO.julie_cpa_collaboration_hub import collaboration_hub

logger = logging.getLogger(__name__)


class IRSNotifier:
    """IRS 변경 알림 처리기"""

    async def notify_agents(self, change_event: IRSChangeEvent):
        """Julie CPA Agent들에게 변경 알림"""
        try:
            # IRS Source Registry 업데이트
            await self._update_irs_registry(change_event)

            # Collaboration Hub를 통한 브로드캐스트
            change_data = {
                "change_event": change_event.to_dict(),
                "impact_assessment": {
                    "severity": change_event.severity,
                    "affected_areas": change_event.affected_areas,
                    "requires_immediate_action": change_event.action_required,
                },
                "recommended_actions": self._generate_recommended_actions(change_event),
            }

            # IRS 변경 알림 메시지 전송
            await collaboration_hub.handle_agent_message(
                "hub", {"message_type": "irs_change_alert", "payload": change_data}
            )

            logger.info(f"Notified Julie CPA agents of IRS change: {change_event.title}")

        except Exception as e:
            logger.error(f"Error notifying agents of change: {e}")

    async def _update_irs_registry(self, change_event: IRSChangeEvent):
        """IRS Source Registry 업데이트"""
        try:
            document_data = {
                "id": f"change_{change_event.event_id}",
                "url": change_event.source_url,
                "title": change_event.title,
                "preview": change_event.content_preview,
                "source": "realtime_monitor",
                "document_type": change_event.change_type,
                "category": "irs_tax",
                "subcategory": change_event.change_type,
                "collected_at": change_event.detected_at,
            }

            # Multimodal RAG에 추가
            await irs_source_registry._add_to_multimodal_rag([document_data])

            # Context7에 등록
            await irs_source_registry._register_to_context7([document_data])

            logger.debug(f"Updated IRS Registry with change: {change_event.event_id}")

        except Exception as e:
            logger.error(f"Error updating IRS Registry: {e}")

    def _generate_recommended_actions(self, change_event: IRSChangeEvent) -> list[str]:
        """변경에 대한 추천 조치 생성"""
        actions = []

        actions.append("Review client tax situations for potential impact")
        actions.append("Update tax calculation algorithms if tax rates changed")
        actions.append("Verify compliance with new filing requirements")

        if change_event.change_type == "tax_rate_change":
            actions.extend(
                [
                    "Recalculate all tax projections",
                    "Update client financial planning models",
                    "Review investment strategies for tax efficiency",
                ]
            )

        elif change_event.change_type == "deduction_change":
            actions.extend(
                [
                    "Update deduction optimization strategies",
                    "Review itemized deduction recommendations",
                    "Assess impact on client tax liabilities",
                ]
            )

        elif change_event.change_type == "deadline_change":
            actions.extend(
                [
                    "Update filing deadline reminders",
                    "Review extension strategies",
                    "Communicate changes to clients",
                ]
            )

        return actions
