"""Voice Interface Models and Constants.

음성 인터페이스 시스템에 필요한 데이터 모델 및 상수 정의.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class VoiceIntent:
    """음성 명령 의도 분석 결과."""

    command_type: str
    intent: str
    confidence: float
    keywords: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    original_text: str = ""


@dataclass
class VoiceResponse:
    """음성 인터페이스 응답."""

    response_type: str
    text: str
    audio_data: bytes | None = None
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# 명령어 유형 상수
COMMAND_TYPES = {
    "tax_analysis": "세금 분석",
    "document_process": "문서 처리",
    "chart_generation": "차트 생성",
    "prediction": "예측",
    "qa": "질의응답",
    "general": "일반 명령",
}
