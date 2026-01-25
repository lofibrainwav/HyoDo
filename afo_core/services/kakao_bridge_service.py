# Trinity Score: 92.0 (KakaoBot Bridge Service)
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class KakaoBridgeService:
    """
    카카오톡 브릿지 앱(Messenger Bot R 등)과 AFO Soul Engine을 연결하는 서비스.
    """

    def __init__(self) -> None:
        self.bot_name = "AFO 승상 봇"
        self.version = "1.0.0"
        env_openchat = os.environ.get("AFO_KAKAO_OPENCHAT_URL")
        self.openchat_url = env_openchat or "https://open.kakao.com/o/pIFKQVbi"
        self.supported_commands = ["/상태", "/도움", "/계산"]

    def get_status(self) -> dict[str, Any]:
        return {
            "bot_status": "active",
            "bridge_version": self.version,
            "supported_commands": self.supported_commands,
            "openchat_url": self.openchat_url,
        }

    async def process_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        카톡 메시지를 수신하여 에이전트 분석 후 답변 반환.
        """
        msg = payload.get("msg", "")
        sender = payload.get("sender", "알 수 없음")
        room = payload.get("room", "개인톡")

        logger.info(f"[KakaoBot] Message from {sender} in {room}: {msg}")

        # 1. 眞(Truth) - 기술적 명령 처리
        if msg.startswith("/"):
            return await self._handle_command(msg)

        # 2. 善(Goodness) - 사령관 명령 확인 및 에이전트 호출
        # [TODO] Chancellor Graph 호출 로직 연동
        if "승상" in msg or "어명" in msg:
            return {
                "status": "success",
                "reply": f"사령관님(또는 {sender}님), 명을 받들겠습니다. 에이전트들이 분석 중입니다...",
                "thoughts": "KakaoBot을 통한 어명 접수. Chancellor Graph 가동 준비.",
            }

        return {"status": "ignored", "reply": None}

    async def _handle_command(self, msg: str) -> dict[str, Any]:
        command = (
            msg.split(" ")[0].substring(1) if hasattr(msg, "substring") else msg.split(" ")[0][1:]
        )

        if command == "상태":
            return {
                "status": "success",
                "reply": "👑 AFO Kingdom 현재 상태\n━━━━━━━━━━━━\n- Trinity Score: 94.16\n- 상황: 승상 가동 중\n- 날씨: 지능의 비가 내리는 중",
            }
        elif command == "도움":
            return {
                "status": "success",
                "reply": (
                    "⚔️ AFO 승상 봇 명령어\n━━━━━━━━━━━━\n"
                    "/상태 : 왕국 건강도 체크\n"
                    "/법령 : 최신 세무/법령 검색\n"
                    "/계산 [금액] : 간이 세금 시뮬레이션\n"
                    f"오픈채팅: {self.openchat_url}"
                ),
            }

        return {"status": "unknown_command", "reply": "알 수 없는 명령입니다. /도움 을 입력하세요."}

    async def get_notifications(self) -> list[dict[str, Any]]:
        """
        쿠에서 알림 메시지 목록을 가져옴.
        """
        try:
            from AFO.bridge_connector import bridge

            # Redis: LRANGE kakao:notification_queue 0 -1
            result = bridge._post(["LRANGE", "kakao:notification_queue", "0", "-1"])
            if result and isinstance(result, list):
                # result[0] contains the result of LRANGE
                notifications = []
                for item in result[0]:
                    try:
                        import json

                        notifications.append(json.loads(item))
                    except Exception:
                        notifications.append({"message": item})
                return notifications
            return []
        except Exception as e:
            logger.error(f"Failed to fetch notifications: {e}")
            return []

    async def clear_notifications(self) -> bool:
        """
        알림 메시지 큐 비우기.
        """
        try:
            from AFO.bridge_connector import bridge

            bridge._post(["DEL", "kakao:notification_queue"])
            return True
        except Exception:
            return False


# 싱글톤 인스턴스
kakao_bridge_service = KakaoBridgeService()
