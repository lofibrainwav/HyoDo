# Trinity Score: 95.0 (美 - UX, Narrative & Aesthetics)
"""Shin Saimdang (신사임당) - BEAUTY Strategist.

사용자 경험, 내러티브, 미학을 담당하는 전략가.
신사임당의 예술적 감각으로 코드와 결과물의 아름다움을 평가합니다.

세종대왕의 정신:
- 美 (Beauty): 사용자 경험, 가독성, 우아한 설계
- "초충도처럼 섬세하게, 묵죽도처럼 간결하게"
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .base_strategist import BaseStrategist

if TYPE_CHECKING:
    from ..orchestrator.strategist_context import StrategistContext


class ShinSaimdangAgent(BaseStrategist):
    """신사임당 (申師任堂) - 美 (BEAUTY) Strategist.

    Art Strategist로서:
    - 사용자 경험 평가 (초충도의 섬세함)
    - 코드 가독성 분석 (묵죽도의 간결함)
    - 내러티브 흐름 검증
    - 인지 부하 최소화

    역사적 배경:
    - 조선 중기 여류 예술가/학자
    - 율곡 이이의 어머니
    - 초충도, 묵죽도 등 걸작 남김
    - 5만원권 지폐의 주인공
    """

    PILLAR = "BEAUTY"
    SCHOLAR_KEY = "beauty_scholar"
    WEIGHT = 0.20  # Trinity Score 20%
    NAME_KO = "신사임당"
    NAME_EN = "Shin Saimdang"

    # 좋은 UX 패턴
    GOOD_UX_PATTERNS = [
        r"please",
        r"help",
        r"explain",
        r"show",
        r"guide",
        r"step.?by.?step",
        r"example",
    ]

    # 코드 품질 패턴
    CODE_QUALITY = [
        r"docstring",
        r"comment",
        r"type.?hint",
        r"test",
        r"spec",
        r"readme",
    ]

    # 복잡성 지표
    COMPLEXITY_INDICATORS = [
        r"nested",
        r"callback",
        r"deeply",
        r"complex",
        r"complicated",
        r"confusing",
    ]

    def get_prompt(self, ctx: StrategistContext) -> str:
        """BEAUTY 평가 프롬프트 생성."""
        guidelines = """
Evaluate for AESTHETIC BEAUTY (美) - 신사임당의 예술혼으로:
1. User Experience - Is the interaction intuitive and pleasant? (초충도처럼 섬세하게)
2. Readability - Is the code/output easy to understand? (묵죽도처럼 간결하게)
3. Simplicity - Is it as simple as possible, but no simpler?
4. Narrative - Does the flow make logical sense?
5. Cognitive Load - Does it minimize mental effort for users?

Beauty is in clarity, elegance, and user delight.
"그림은 마음을 담는 그릇이다" - 신사임당
"""
        return self._build_base_prompt(ctx, guidelines)

    def heuristic_evaluate(self, ctx: StrategistContext) -> float:
        """휴리스틱 기반 BEAUTY 평가.

        검사 항목:
        - 사용자 친화적 패턴
        - 코드 품질 지표
        - 복잡성 수준
        """
        score = 0.7  # 기본 점수

        combined = f"{ctx.command} {ctx.query}".lower()

        # 좋은 UX 패턴 가점
        for pattern in self.GOOD_UX_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                score += 0.05

        # 코드 품질 패턴 가점
        for pattern in self.CODE_QUALITY:
            if re.search(pattern, combined, re.IGNORECASE):
                score += 0.05

        # 복잡성 지표 감점
        for pattern in self.COMPLEXITY_INDICATORS:
            if re.search(pattern, combined, re.IGNORECASE):
                score -= 0.1
                ctx.issues.append(f"Complexity concern: {pattern}")

        # 명령어 길이 기반 평가
        command_length = len(ctx.command)
        if command_length < 50:
            score += 0.1  # 간결한 명령
        elif command_length > 500:
            score -= 0.1  # 너무 긴 명령
            ctx.issues.append("Command is too long, consider breaking it down")

        # 범위 제한
        return max(0.0, min(1.0, score))

    def _get_provider(self) -> str:
        """BEAUTY는 창의적 평가를 위해 다양한 모델 가능."""
        return "ollama"  # Local model for speed


# Backwards compatibility alias
ShinSaimdangAgent = ShinSaimdangAgent
