# Trinity Score: 90.0 (Established by Chancellor)
"""
Detailed Pillars Calculator (Phase 16)
"Comprehensive 5-Pillar Metrics" - 선, 미, 효, 영 지표 상세 계산기
PDF 평가 기준: 각 기둥별 세부 구현 완성도 평가
"""

import logging
from typing import Any

from AFO.utils.standard_shield import shield

logger = logging.getLogger("AFO.PillarsMetrics")


class DetailedPillarsCalculator:
    """
    DetailedPillarsCalculator: 선, 미, 효, 영 점수 계산기
    """

    @shield(default_return=0.0, pillar="善")
    def calculate_goodness_score(self, context: dict[str, Any]) -> float:
        """
        선 (Goodness) - 35%: 윤리, 안정성, 리스크 관리
        Target: Risk Score <= 0.1, Ethical Guardrails Active
        """
        score = 0.0
        # 1. Risk Score (Max 0.4)
        risk = context.get("risk_level", 0.0)
        if risk <= 0.1:
            score += 0.4
        elif risk <= 0.5:
            score += 0.2

        # 2. Ethical Guardrails (Max 0.3)
        if context.get("ethics_check"):
            score += 0.3

        # 3. Vulnerabilities (Max 0.2)
        if context.get("vulnerabilities", 0) == 0:
            score += 0.2

        # 4. Cost Optimization (Max 0.1)
        if context.get("cost_optimized"):
            score += 0.1

        return round(score, 2)  # 0.0 ~ 1.0

    @shield(default_return=0.0, pillar="美")
    def calculate_beauty_score(self, code_snippet: str, context: dict[str, Any]) -> float:
        """
        미 (Beauty) - 20%: 미학, 단순함, UX 우아함
        Target: Modularity, Naming Consistency, Glassmorphism
        """
        score = 0.0
        # 1. Modularity (Max 0.4)
        if "class " in code_snippet and "def " in code_snippet:
            score += 0.4

        # 2. Naming Consistency (Max 0.2)
        # Simple heuristic: no snake_case mixed with camelCase in typical Python (snake_case preferred)
        if ("_" in code_snippet and "Variable" not in code_snippet) or context.get(
            "style_guide_passed"
        ):  # Very rough heuristic
            score += 0.2

        # 3. UX Elegance (Max 0.3) - For UI code or System Status
        if context.get("ux_theme") == "Glassmorphism" or "Trinity Glow" in context.get(
            "features", []
        ):
            score += 0.3

        # 4. Simplicity (Max 0.1)
        if len(code_snippet.splitlines()) < 500:
            score += 0.1

        return round(score, 2)

    def calculate_serenity_score(self, context: dict[str, Any]) -> float:
        """
        효 (Serenity) - 8%: 평온, 마찰 제거, 자동화
        Target: Automation, Speed < 1s, Env Consistency
        """
        score = 0.0
        # 1. Automation Level (Max 0.4)
        if context.get("mode") == "AUTO_RUN" or context.get("auto_deploy"):
            score += 0.4

        # 2. Execution Speed (Max 0.3)
        duration = context.get("duration_ms", 0)
        if duration < 1000:  # < 1s
            score += 0.3

        # 3. Env Consistency (Max 0.2)
        if context.get("env_consistent"):
            score += 0.2

        # 4. SSE Streaming (Max 0.1)
        if context.get("sse_active"):
            score += 0.1

        return round(score, 2)

    def calculate_eternity_score(self, code_snippet: str, context: dict[str, Any]) -> float:
        """
        영 (Eternity) - 2%: 영속성, 지속 가능성, 문서화
        Target: Docs, Git, Evolution Logs
        """
        score = 0.0
        # 1. Documentation (Max 0.4)
        if '"""' in code_snippet or "'''" in code_snippet:
            score += 0.4

        # 2. Evolution Log (Max 0.3)
        if context.get("evolution_logged"):
            score += 0.3

        # 3. Version Control (Max 0.2)
        if context.get("git_tracked"):
            score += 0.2

        # 4. Sustainability (Max 0.1)
        if context.get("sustainable_arch"):
            score += 0.1

        return round(score, 2)


# Singleton Instance
pillars_metrics = DetailedPillarsCalculator()
