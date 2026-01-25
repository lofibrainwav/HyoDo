"""Trinity Metrics

Trinity Score 메트릭 모델 및 관리 로직.
"""

from typing import Any


class TrinityMetrics:
    """
    Trinity Score 메트릭 (眞善美孝永 5기둥)

    Trinity Score: 95+ AUTO_RUN, 70-89 ASK_COMMANDER, <70 BLOCK
    """

    pillars: dict[str, float]
    auto_run_condition: str
    overall_score: float

    def __post_init__(self) -> None:
        if not self.pillars:
            self.pillars = {
                "truth": 95.0,
                "goodness": 94.0,
                "beauty": 96.0,
                "serenity": 94.0,
                "eternity": 92.0,
            }
            self.auto_run_condition = "Trinity Score ≥ 90 AND Risk Score ≤ 10"
            self.overall_score = sum(self.pillars.values())

    def update_score(self, pillar: str, new_score: float) -> dict[str, Any]:
        """특정 기둥 점수 업데이트"""
        old_score = self.pillars.get(pillar, 0.0)
        self.pillars[pillar] = new_score

        # 전체 점수 재계산
        self.overall_score = sum(self.pillars.values())

        return {
            "pillar": pillar,
            "old_score": old_score,
            "new_score": new_score,
            "change": new_score - old_score,
            "overall_score": self.overall_score,
        }

    def calculate_decision(self, risk_score: float) -> str:
        """Trinity Gate 결정"""
        if self.overall_score >= 90 and risk_score <= 10:
            self.auto_run_condition = "AUTO_RUN (Trinity Score ≥ 90 AND Risk Score ≤ 10)"
            return "AUTO_RUN"
        elif self.overall_score >= 70 and risk_score <= 10:
            return "ASK_COMMANDER"
        else:
            return "BLOCK"

    def get_metrics_summary(self) -> dict[str, Any]:
        """메트릭 요약 조회"""
        return {
            "pillars": self.pillars.copy(),
            "auto_run_condition": self.auto_run_condition,
            "overall_score": self.overall_score,
            "decision": self.calculate_decision(5.0),  # Default risk score
        }
