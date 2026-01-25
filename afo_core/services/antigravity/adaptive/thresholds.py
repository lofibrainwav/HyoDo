# Trinity Score: 90.0 (Established by Chancellor)
"""
Antigravity Adaptive Thresholds - 동적 임계값 조정 모듈
프로젝트 맥락과 히스토리를 기반으로 임계값 자동 조정
"""

import logging
from typing import Any

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
)

logger = logging.getLogger(__name__)


class AdaptiveThresholds:
    """
    동적 임계값 관리자
    프로젝트 특성과 히스토리를 고려한 임계값 조정
    """

    def __init__(self) -> None:
        # 기본 임계값 (SSOT: trinity_ssot.py)
        self.base_thresholds = {
            "auto_run_min_score": THRESHOLD_AUTO_RUN_SCORE,
            "auto_run_max_risk": THRESHOLD_AUTO_RUN_RISK,
            "manual_review_min_score": 70.0,
            "block_threshold_score": 50.0,
            "adaptation_rate": 0.1,  # 학습률
            "history_window_days": 30,
            "min_samples_for_prediction": 10,
        }

    def calculate_dynamic_thresholds(self, context: dict[str, Any]) -> dict[str, float]:
        """
        동적 임계값 계산
        프로젝트 맥락과 히스토리를 기반으로 임계값 조정

        Args:
            context: 프로젝트 맥락 정보

        Returns:
            조정된 임계값들
        """
        base_thresholds = self.base_thresholds.copy()

        # 프로젝트 크기 기반 조정
        project_size = context.get("project_size", "medium")
        size_multipliers = {
            "small": 0.9,  # 작은 프로젝트는 관대
            "medium": 1.0,
            "large": 1.1,  # 큰 프로젝트는 엄격
        }
        size_multiplier = size_multipliers.get(project_size, 1.0)

        # 팀 경험도 기반 조정
        team_experience = context.get("team_experience", "intermediate")
        experience_multipliers = {
            "beginner": 0.8,
            "intermediate": 1.0,
            "expert": 1.2,
        }
        experience_multiplier = experience_multipliers.get(team_experience, 1.0)

        # 시간 압박 고려
        time_pressure = context.get("time_pressure", "normal")
        time_multipliers = {
            "low": 1.2,  # 여유로움: 엄격
            "normal": 1.0,
            "high": 0.9,  # 급함: 관대
        }
        time_multiplier = time_multipliers.get(time_pressure, 1.0)

        # 종합 조정 계수
        adjustment_factor = size_multiplier * experience_multiplier * time_multiplier

        return {
            "auto_run_min_score": base_thresholds["auto_run_min_score"] * adjustment_factor,
            "auto_run_max_risk": base_thresholds["auto_run_max_risk"] / adjustment_factor,
            "manual_review_min_score": base_thresholds["manual_review_min_score"]
            * adjustment_factor,
            "block_threshold_score": base_thresholds["block_threshold_score"] * adjustment_factor,
        }

    def adjust_for_context(
        self, thresholds: dict[str, float], context: dict[str, Any]
    ) -> dict[str, float]:
        """
        맥락 기반 추가 임계값 조정
        코드 변경의 특성을 고려한 미세 조정

        Args:
            thresholds: 기본 임계값
            context: 맥락 정보

        Returns:
            추가 조정된 임계값
        """
        adjusted = thresholds.copy()

        # 변경 범위 고려
        change_scope = context.get("change_scope", "small")
        scope_adjustments = {
            "small": -5.0,  # 작은 변경: 관대
            "medium": 0.0,
            "large": 5.0,  # 큰 변경: 엄격
            "breaking": 10.0,  # 호환성 깨는 변경: 매우 엄격
        }
        scope_adjustment = scope_adjustments.get(change_scope, 0.0)
        adjusted["auto_run_min_score"] += scope_adjustment

        # 테스트 커버리지 고려
        test_coverage = context.get("test_coverage", 80.0)
        coverage_adjustment = (test_coverage - 80.0) * 0.1  # 80% 기준
        adjusted["auto_run_min_score"] += coverage_adjustment

        # CI 상태 고려
        ci_status = context.get("ci_status", "passing")
        if ci_status == "failing":
            adjusted["auto_run_min_score"] += 10.0  # CI 실패 시 엄격

        return adjusted

    def adapt_thresholds(self, quality_history: list) -> dict[str, Any]:
        """
        동적 임계값 적응
        히스토리 데이터를 기반으로 임계값 자동 조정

        Args:
            quality_history: 품질 히스토리 데이터

        Returns:
            적응 결과
        """
        if len(quality_history) < 20:
            return {"status": "insufficient_data"}

        try:
            # 최근 성과 분석
            recent_decisions = quality_history[-50:]  # 최근 50개

            # AUTO_RUN 성공률 계산
            auto_run_decisions = [d for d in recent_decisions if d["decision"] == "AUTO_RUN"]
            successful_auto_runs = len(
                [d for d in auto_run_decisions if d.get("outcome") == "success"]
            )

            if auto_run_decisions:
                success_rate = successful_auto_runs / len(auto_run_decisions)

                # 성공률 기반 임계값 조정
                if success_rate > 0.95:  # 너무 높음: 관대하게
                    self.base_thresholds["auto_run_min_score"] -= 1.0
                elif success_rate < 0.80:  # 너무 낮음: 엄격하게
                    self.base_thresholds["auto_run_min_score"] += 1.0

            return {
                "status": "adapted",
                "new_thresholds": self.base_thresholds.copy(),
                "success_rate": success_rate if "success_rate" in locals() else None,
            }

        except Exception as e:
            logger.exception(f"임계값 적응 실패: {e}")
            return {"status": "error", "message": str(e)}


# 싱글톤 인스턴스
adaptive_thresholds = AdaptiveThresholds()
