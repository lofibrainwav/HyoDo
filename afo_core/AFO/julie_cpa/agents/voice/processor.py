"""Voice Command Processor.

음성 인식(STT) 및 자연어 의도 분석(NLU).
"""

from __future__ import annotations

import re

from .models import VoiceIntent


class VoiceProcessor:
    """음성 명령 해석기."""

    async def transcribe(self, audio_data: bytes) -> str:
        """음성 데이터를 텍스트로 변환합니다 (STT)."""
        # 실제 구현에서는 Whisper API 등을 호출
        # 현재는 모의 텍스트 반환
        return "올해 예상 세금을 계산해줘"

    async def analyze_intent(self, text: str) -> VoiceIntent:
        """텍스트에서 의도를 분석합니다 (NLU)."""
        command_type = self._classify_type(text)
        keywords = self._extract_keywords(text, command_type)

        return VoiceIntent(
            command_type=command_type,
            intent="calculate_tax",
            confidence=0.95,
            keywords=keywords,
            original_text=text,
        )

    def _classify_type(self, text: str) -> str:
        """텍스트에 기반하여 명령 유형을 분류합니다."""
        if any(w in text for w in ["세금", "계산", "절세"]):
            return "tax_analysis"
        if any(w in text for w in ["차트", "그래프", "그려"]):
            return "chart_generation"
        if any(w in text for w in ["문서", "파일", "읽어"]):
            return "document_process"
        return "general"

    def _extract_keywords(self, text: str, command_type: str) -> list[str]:
        """핵심 키워드를 추출합니다."""
        # 정규표현식 등을 사용한 간단한 추출
        keywords = re.findall(r"[가-힣]+", text)
        return [k for k in keywords if len(k) > 1]
