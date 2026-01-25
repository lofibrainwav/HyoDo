"""Voice Interface System Package.

음성으로 제어하는 CPA 인터페이스.
음성 인식, 의도 분석, 기능 실행, 음성 합성 통합 제공.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from .executor import VoiceExecutor
from .models import COMMAND_TYPES, VoiceIntent, VoiceResponse
from .processor import VoiceProcessor


class CPAVoiceInterfaceSystem:
    """CPA 음성 인터페이스 시스템 (Facade)."""

    def __init__(self) -> None:
        self.processor = VoiceProcessor()
        self.executor = VoiceExecutor()
        self.sessions: dict[str, dict[str, Any]] = {}

    async def process_voice_command(
        self,
        audio_data: bytes,
        session_id: str = None,
        user_context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """음성 명령을 처리하고 응답을 생성합니다."""
        # 1. STT
        text = await self.processor.transcribe(audio_data)

        # 2. NLU
        intent = await self.processor.analyze_intent(text)

        # 3. Execution
        if not session_id:
            session_id = f"voice_{datetime.now().timestamp()}"

        result = await self.executor.execute(intent, user_context or {})

        # 4. Response generation
        audio_response = await self._synthesize_voice(result.get("message", "처리를 완료했습니다."))

        return {
            "success": True,
            "session_id": session_id,
            "transcription": text,
            "intent": intent.command_type,
            "result": result,
            "voice_response": {"text": result.get("message"), "audio_base64": audio_response},
        }

    async def _synthesize_voice(self, text: str) -> str:
        """텍스트를 음성으로 변환(TTS)하여 Base64로 반환합니다."""
        # 실제 구현에서는 ElevenLabs API 등을 호출
        # 현재는 가상 데이터 반환
        return "BASE64_AUDIO_DATA_MOCK"


__all__ = ["CPAVoiceInterfaceSystem", "VoiceIntent", "VoiceResponse"]
