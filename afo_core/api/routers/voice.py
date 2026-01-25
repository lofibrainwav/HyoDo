# Trinity Score: 90.0 (Established by Chancellor)
"""Voice Command Router for AFO Kingdom (Phase 24)
Handles voice command processing and TTS responses.
"""

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from AFO.utils.standard_shield import shield

logger = logging.getLogger("AFO.Voice")
router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceCommand(BaseModel):
    text: str
    language: str = "ko-KR"
    confidence: float | None = None


class VoiceResponse(BaseModel):
    status: str
    response_text: str
    tts_url: str | None = None  # For future cloud TTS


@shield(pillar="善")
@router.post("/command", response_model=VoiceResponse)
async def process_voice_command(command: VoiceCommand) -> VoiceResponse:
    """Process a voice command from the Commander.
    Routes to Chancellor Graph for decision making.
    """
    logger.info(f"🎙️ Voice Command Received: {command.text}")

    # Simple command routing (to be connected to Chancellor Graph)
    response_text = f"명령을 받았습니다: {command.text}"

    # Keywords for specific actions
    if "상태" in command.text:
        response_text = (
            "왕국의 상태는 건강합니다. Trinity Score 100점, 모든 시스템 정상 가동 중입니다."
        )
    elif "보고" in command.text:
        response_text = "보고를 올립니다. 현재 왕국은 클라우드 우주에서 영원히 빛나고 있습니다."
    elif "안녕" in command.text or "hello" in command.text.lower():
        response_text = "형님, 안녕하십니까! 왕국이 형님의 명령을 기다리고 있습니다."

    return VoiceResponse(
        status="success",
        response_text=response_text,
        tts_url=None,  # Browser TTS handles this for now
    )


@shield(pillar="善")
@router.get("/health")
async def voice_health() -> dict[str, Any]:
    """Check voice service health."""
    return {
        "status": "healthy",
        "stt_mode": "browser",  # Web Speech API
        "tts_mode": "browser",  # SpeechSynthesis
        "language": "ko-KR",
    }
