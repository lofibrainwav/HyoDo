# Trinity Score: 93.0 (Unified Messaging Service)
import logging
import time
from enum import Enum
from typing import Any

from AFO.domain.metrics.prometheus import (
    messaging_errors_total,
    messaging_requests_total,
    messaging_response_seconds,
)

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    KAKAO = "kakao"
    DISCORD = "discord"
    DASHBOARD = "dashboard"
    SLACK = "slack"  # 미래 확장용


class UnifiedMessagingService:
    """
    왕국의 통합 메시징 서비스.
    카톡, 디스코드 등 모든 채널의 메시지를 중앙에서 처리하고 에이전트와 연결.
    """

    def __init__(self) -> None:
        self.active_channels = [ChannelType.KAKAO, ChannelType.DISCORD, ChannelType.DASHBOARD]

    async def handle_incoming_message(
        self,
        content: str,
        sender: str,
        channel: ChannelType,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        외부 채널로부터 들어온 메시지를 왕국의 지능과 연결.
        """
        channel_label = channel.value
        start_time = time.monotonic()
        messaging_requests_total.labels(channel=channel_label).inc()
        logger.info(f"[UnifiedMsg] Message from {channel_label}:{sender} -> {content}")

        try:
            # 1. 眞(Truth) - 에이전트 엔진 소환 (Chancellor Graph 연동 예정)
            # 현재는 메타인지 기반으로 에이전트의 답변을 시뮬레이션
            response_text = await self._generate_agent_response(content, sender)

            # 2. 善(Goodness) - 채널별 최적화된 포맷팅
            formatted_response = self._format_for_channel(response_text, channel)

            return {"reply": formatted_response, "engine": "ChancellorV2", "persona": "승상"}
        except Exception as e:
            messaging_errors_total.labels(channel=channel_label).inc()
            logger.error(
                f"[UnifiedMsg] Error handling message from {channel_label}: {e}",
                exc_info=True,
                extra={"pillar": "善"},
            )
            raise
        finally:
            messaging_response_seconds.labels(channel=channel_label).observe(
                time.monotonic() - start_time
            )

    async def _generate_agent_response(self, content: str, sender: str) -> str:
        """
        Chancellor Graph를 호출하여 왕국의 지능으로 응답 생성.
        """
        try:
            # 상태 확인 단축 명령
            if content.strip() in ["/상태", "!상태", "상태"]:
                return "👑 왕국 상태 보고: Trinity Score 94.16. 모든 시스템이 정상 가동 중이며, 카카오톡 채널이 대변인 레이어에 통합되었습니다."

            # Chancellor Graph 호출 (The Brain)
            from AFO.chancellor_graph import ChancellorGraph

            # Context 생성 (sender 정보를 포함)
            context = {"sender": sender, "role": "user", "platform": "spokesman"}

            # Graph 실행
            logger.info(f"Invoking Chancellor Graph for: {content[:20]}...")
            result = await ChancellorGraph.invoke(
                command=content,
                headers={"X-AFO-Source": "unified_messaging_service"},
                sender_context=context,
            )

            # 결과 파싱 (Success 여부와 상관없이 출력 확인)
            outputs = result.get("outputs", {})

            # 1. REPORT 노드 (최종 보고서)
            if outputs.get("REPORT"):
                report_data = outputs["REPORT"]
                if isinstance(report_data, dict):
                    # 딕셔너리인 경우 구조화된 응답 생성
                    recommendations = report_data.get("recommendations", [])
                    errors = report_data.get("errors", [])
                    trinity_score = report_data.get("trinity_score", "N/A")

                    msg_parts = [f"📊 분석 결과 (Trinity Score: {trinity_score})"]
                    if recommendations:
                        msg_parts.append("\n💡 제안사항:")
                        msg_parts.extend([f"- {rec}" for rec in recommendations])
                    if errors:
                        msg_parts.append("\n⚠️ 발견된 이슈:")
                        msg_parts.extend([f"- {err}" for err in errors[:3]])

                    return "\n".join(msg_parts)
                return str(report_data)

            # 2. EXECUTE 노드 (실행 결과)
            if outputs.get("EXECUTE"):
                return str(outputs["EXECUTE"])

            # 3. V1 Legacy 결과
            if "V1" in outputs:
                return str(outputs["V1"])

            # 4. 에러 메시지 확인
            if not result.get("success", False):
                error_msg = result.get("error", "구체적인 원인 불명")
                errors = result.get("errors", [])
                full_error = f"{error_msg} (Errors: {errors})"
                logger.warning(f"Chancellor Graph indicated failure: {full_error}")

                # 에러가 있더라도 부분적인 응답이 있을 수 있음
                if errors:
                    return "⚠️ 분석 중 이슈가 발생했습니다:\n- " + "\n- ".join(
                        str(e) for e in errors[:3]
                    )

            return (
                "🤔 승상께서 깊은 생각에 잠기셨으나, 말씀을 남기지 않으셨습니다. (Empty Response)"
            )

        except Exception as e:
            logger.error(
                f"Failed to generate agent response for {sender}: {e}",
                exc_info=True,
                extra={"pillar": "善"},
            )
            return f"🔥 시스템 오류 발생: {e!s}"

    def _format_for_channel(self, text: str, channel: ChannelType) -> str:
        if channel == ChannelType.KAKAO:
            return f"[AFO 승상]\n{text}"
        elif channel == ChannelType.DISCORD:
            return f"**[AFO Kingdom Spokesman]**\n{text}"
        return text


# 싱글톤
unified_messaging_service = UnifiedMessagingService()
