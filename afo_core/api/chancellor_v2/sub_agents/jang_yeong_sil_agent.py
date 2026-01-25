# Trinity Score: 95.0 (眞 - Technical Truth & Architecture)
"""Jang Yeong-sil (장영실) - TRUTH Strategist.

기술적 진실과 아키텍처를 담당하는 전략가.
조선 최고의 과학자 장영실의 정밀함으로 코드의 정확성과 구조적 건전성을 평가합니다.

세종대왕의 정신:
- 眞 (Truth): 기술적 정확성, 타입 안전성, 아키텍처 일관성
- "측우기처럼 정확하게, 자격루처럼 정밀하게"
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .base_strategist import BaseStrategist

if TYPE_CHECKING:
    from ..orchestrator.strategist_context import StrategistContext


class JangYeongSilAgent(BaseStrategist):
    """장영실 (蔣英實) - 眞 (TRUTH) Strategist.

    Technical Strategist로서:
    - 코드 정확성 평가 (측우기의 정밀함)
    - 아키텍처 건전성 분석 (자격루의 체계)
    - 타입 안전성 검증
    - 기술적 리스크 식별

    역사적 배경:
    - 조선 세종대왕 시대 최고의 과학자/발명가
    - 측우기, 자격루, 혼천의 등 발명
    - 노비 출신에서 종3품까지 오른 실력주의의 상징
    """

    PILLAR = "TRUTH"
    SCHOLAR_KEY = "truth_scholar"
    WEIGHT = 0.35  # Trinity Score 35%
    NAME_KO = "장영실"
    NAME_EN = "Jang Yeong-sil"

    # 기술적 위험 키워드
    RISK_KEYWORDS = [
        "eval",
        "exec",
        "subprocess",
        "os.system",
        "pickle",
        "yaml.load",
        "shell=True",
        "__import__",
        "globals()",
        "locals()",
    ]

    # 안전 패턴
    SAFE_PATTERNS = [
        r"typing\.",
        r"Pydantic",
        r"dataclass",
        r"async def",
        r"await",
        r"try:",
        r"except",
    ]

    def get_prompt(self, ctx: StrategistContext) -> str:
        """TRUTH 평가 프롬프트 생성."""
        guidelines = """
Evaluate for TECHNICAL TRUTH (眞) - 장영실의 정밀함으로:
1. Code correctness - Does the logic achieve the intended goal? (측우기처럼 정확하게)
2. Type safety - Are types properly defined and used?
3. Architecture - Does it follow established patterns? (자격루처럼 체계적으로)
4. Security - Are there any dangerous patterns (eval, exec, etc.)?
5. Performance - Any obvious inefficiencies?

Focus on objective, verifiable technical facts.
"기술은 거짓을 말하지 않는다" - 장영실
"""
        return self._build_base_prompt(ctx, guidelines)

    def heuristic_evaluate(self, ctx: StrategistContext) -> float:
        """휴리스틱 기반 TRUTH 평가.

        검사 항목:
        - 위험 키워드 존재 여부
        - 안전 패턴 사용 여부
        - 명령어 길이 및 복잡도
        """
        score = 0.7  # 기본 점수

        command = ctx.command.lower()
        query = ctx.query.lower()
        combined = f"{command} {query}"

        # 위험 키워드 감점
        for keyword in self.RISK_KEYWORDS:
            if keyword.lower() in combined:
                score -= 0.15
                ctx.issues.append(f"Dangerous pattern detected: {keyword}")

        # 안전 패턴 가점
        for pattern in self.SAFE_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                score += 0.05

        # Skill 기반 조정
        skill_id = ctx.skill_id.lower()
        if skill_id in ["read", "search", "analyze"]:
            score += 0.1  # 읽기 전용 작업은 안전
        elif skill_id in ["write", "delete", "execute"]:
            score -= 0.05  # 쓰기 작업은 주의

        # 범위 제한
        return max(0.0, min(1.0, score))

    def _get_provider(self) -> str:
        """TRUTH는 정확성이 중요하므로 고품질 모델 사용."""
        return "anthropic"  # Claude for technical accuracy


# Backwards compatibility alias
ZhugeLiangAgent = JangYeongSilAgent
