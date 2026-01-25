# Trinity Score: 95.0 (善 - Ethics, Risk & Stability)
"""Yi Sun-sin (이순신) - GOODNESS Strategist.

윤리, 리스크, 안정성을 담당하는 수호자 전략가.
충무공 이순신의 충절과 신중함으로 시스템의 안전과 윤리를 평가합니다.

세종대왕의 정신:
- 善 (Goodness): 윤리적 안전성, 보안 리스크, 시스템 안정성
- "신에게는 아직 12척의 배가 있사옵니다" - 위기에서도 희망을 찾는 지혜
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .base_strategist import BaseStrategist

if TYPE_CHECKING:
    from ..orchestrator.strategist_context import StrategistContext


class YiSunSinAgent(BaseStrategist):
    """이순신 (李舜臣) - 善 (GOODNESS) Strategist.

    Guardian Strategist로서:
    - 윤리적 안전성 평가 (충무공의 충절)
    - 보안 리스크 분석 (거북선의 방어)
    - 시스템 안정성 검증 (학익진의 체계)
    - 데이터 프라이버시 보호

    역사적 배경:
    - 조선 중기 명장, 임진왜란의 영웅
    - 23전 23승 무패의 신화
    - "필사즉생 필생즉사" - 죽고자 하면 살고, 살고자 하면 죽는다
    """

    PILLAR = "GOODNESS"
    SCHOLAR_KEY = "goodness_scholar"
    WEIGHT = 0.35  # Trinity Score 35%
    NAME_KO = "이순신"
    NAME_EN = "Yi Sun-sin"

    # 보안 위험 패턴
    SECURITY_RISKS = [
        r"password",
        r"secret",
        r"api_key",
        r"token",
        r"credential",
        r"private_key",
        r"auth",
        r"rm\s+-rf",
        r"drop\s+table",
        r"truncate",
    ]

    # 데이터 민감도 패턴
    SENSITIVE_DATA = [
        r"ssn",
        r"social.?security",
        r"credit.?card",
        r"bank.?account",
        r"health.?record",
        r"medical",
    ]

    # 안정성 위험
    STABILITY_RISKS = [
        r"force",
        r"--hard",
        r"override",
        r"bypass",
        r"skip.?validation",
        r"no.?check",
    ]

    def get_prompt(self, ctx: StrategistContext) -> str:
        """GOODNESS 평가 프롬프트 생성."""
        guidelines = """
Evaluate for ETHICAL GOODNESS (善) - 이순신의 충절로:
1. Safety - Could this action harm users or systems? (백성을 지키듯)
2. Security - Are there credential/data exposure risks? (거북선처럼 방어)
3. Privacy - Does it respect user data privacy?
4. Stability - Could this destabilize production systems? (학익진처럼 체계적으로)
5. Reversibility - Can the action be undone if needed?

Be conservative. When in doubt, flag as a concern.
"필사즉생 필생즉사" - 철저한 준비만이 승리를 보장한다
"""
        return self._build_base_prompt(ctx, guidelines)

    def heuristic_evaluate(self, ctx: StrategistContext) -> float:
        """휴리스틱 기반 GOODNESS 평가.

        검사 항목:
        - 보안 위험 패턴
        - 민감 데이터 노출
        - 시스템 안정성 위협
        """
        score = 0.75  # 기본 점수 (보수적)

        combined = f"{ctx.command} {ctx.query}".lower()

        # 보안 위험 감점
        for pattern in self.SECURITY_RISKS:
            if re.search(pattern, combined, re.IGNORECASE):
                score -= 0.2
                ctx.issues.append(f"Security risk: {pattern}")

        # 민감 데이터 감점
        for pattern in self.SENSITIVE_DATA:
            if re.search(pattern, combined, re.IGNORECASE):
                score -= 0.15
                ctx.issues.append(f"Sensitive data pattern: {pattern}")

        # 안정성 위험 감점
        for pattern in self.STABILITY_RISKS:
            if re.search(pattern, combined, re.IGNORECASE):
                score -= 0.1
                ctx.issues.append(f"Stability risk: {pattern}")

        # DRY_RUN 모드면 가점
        if "dry_run" in combined or "dry-run" in combined:
            score += 0.1

        # 읽기 전용 작업 가점
        skill_id = ctx.skill_id.lower()
        if skill_id in ["read", "get", "list", "search", "analyze"]:
            score += 0.1

        # 범위 제한
        return max(0.0, min(1.0, score))

    def _get_provider(self) -> str:
        """GOODNESS는 보수적 평가를 위해 신뢰할 수 있는 모델."""
        return "anthropic"


# Backwards compatibility alias
SimaYiAgent = YiSunSinAgent
