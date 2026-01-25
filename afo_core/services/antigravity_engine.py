# Trinity Score: 90.0 (Established by Chancellor)
"""
Antigravity Engine - Phase 6 고급 거버넌스 시스템
Trinity Score 기반 지능형 코드 품질 관리
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
)

logger = logging.getLogger(__name__)


# Lazy import to avoid circular dependency
try:
    from services.protocol_officer import ProtocolOfficer
except ImportError:
    ProtocolOfficer = None  # type: ignore[assignment, misc]

try:
    from services.antigravity_reporter import AntigravityReporter
except ImportError:
    AntigravityReporter = None  # type: ignore[assignment]

# Lazy import for antigravity settings
try:
    from config.antigravity import antigravity
except ImportError:
    antigravity = None  # type: ignore[assignment]


class AntigravityEngine:
    """
    Antigravity Engine - 지능형 품질 게이트 시스템
    Trinity Score 기반 ML 예측 및 동적 임계값 조정
    """

    def __init__(self, protocol_officer: Any | None = None) -> None:
        self.quality_history: list[dict[str, Any]] = []
        self.prediction_model = None
        self.dynamic_thresholds = self._initialize_thresholds()

        # [Phase B] Protocol Officer 주입
        if protocol_officer is None and ProtocolOfficer is not None:
            from services.protocol_officer import protocol_officer as default_officer

            self.protocol_officer = default_officer
        elif protocol_officer is None:
            raise ValueError(
                "[SSOT] Protocol Officer is required. Cannot initialize AntigravityEngine without Protocol Officer."
            )
        else:
            self.protocol_officer = protocol_officer

        # Initialize Reporter
        if AntigravityReporter:
            self.reporter = AntigravityReporter(self.protocol_officer)
        else:
            logger.warning("AntigravityReporter module not found. Reporting capabilities limited.")
            self.reporter = None

    def _initialize_thresholds(self) -> dict[str, Any]:
        """기본 동적 임계값 초기화 (SSOT: trinity_ssot.py)"""
        return {
            "auto_run_min_score": THRESHOLD_AUTO_RUN_SCORE,
            "auto_run_max_risk": THRESHOLD_AUTO_RUN_RISK,
            "manual_review_min_score": 70.0,
            "block_threshold_score": 50.0,
            "adaptation_rate": 0.1,  # 학습률
            "history_window_days": 30,
            "min_samples_for_prediction": 10,
        }

    async def evaluate_quality_gate(
        self, trinity_score: float, risk_score: float, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        지능형 품질 게이트 평가
        ML 예측과 동적 임계값을 활용한 의사결정
        """
        # 1. ML 기반 예측 (향후 품질 추정)
        predicted_score = await self._predict_future_quality(trinity_score, context)

        # 2. 동적 임계값 계산
        dynamic_thresholds = await self._calculate_dynamic_thresholds(context)

        # 3. 컨텍스트 기반 조정
        adjusted_thresholds = await self._adjust_for_context(dynamic_thresholds, context)

        # 4. 최종 의사결정
        decision = await self._make_intelligent_decision(
            trinity_score, risk_score, predicted_score, adjusted_thresholds, context
        )

        # 5. 학습 데이터 수집
        await self._collect_learning_data(trinity_score, risk_score, context, decision)

        result = {
            "decision": decision,
            "trinity_score": trinity_score,
            "risk_score": risk_score,
            "predicted_score": predicted_score,
            "dynamic_thresholds": adjusted_thresholds,
            "confidence": await self._calculate_confidence(decision, context),
            "recommendations": await self._generate_recommendations(decision, context),
        }

        # [Phase B] Protocol Officer를 통한 메시지 포맷팅 (완전 강제 - 우회 불가)
        if self.protocol_officer is None:
            raise ValueError(
                "[SSOT] Protocol Officer is required. Cannot format message without Protocol Officer."
            )

        # 결정 메시지를 Protocol Officer로 포맷팅 (무조건 거침)
        decision_msg = self._format_decision_message(result)
        result["formatted_message"] = self.protocol_officer.compose_diplomatic_message(
            decision_msg, audience=self.protocol_officer.AUDIENCE_COMMANDER
        )

        return result

    async def _predict_future_quality(self, current_score: float, context: dict[str, Any]) -> float:
        """ML 기반 미래 품질 예측"""
        if len(self.quality_history) < self.dynamic_thresholds["min_samples_for_prediction"]:
            return current_score

        try:
            # 최근 히스토리 분석 (지난 30일)
            self.quality_history = [
                h
                for h in self.quality_history
                if (datetime.now(UTC) - h["timestamp"]).days
                <= self.dynamic_thresholds["history_window_days"]
            ]

            if len(self.quality_history) < 5:
                return current_score

            # 간단한 추세 분석
            scores = [h["trinity_score"] for h in self.quality_history[-10:]]  # 최근 10개
            if len(scores) >= 2:
                trend_result = np.polyfit(range(len(scores)), scores, 1)
                trend = float(trend_result[0])

                # 추세 기반 예측 (다음 3회 커밋 후 예상 점수)
                prediction_steps = 3
                predicted = float(scores[-1]) + (trend * prediction_steps)
                return max(0.0, min(100.0, predicted))

        except Exception as e:
            logger.warning(f"품질 예측 실패: {e}")

        return current_score

    async def _calculate_dynamic_thresholds(self, context: dict[str, Any]) -> dict[str, float]:
        """동적 임계값 계산"""
        base_thresholds = self.dynamic_thresholds.copy()

        # 프로젝트 크기, 팀 경험도, 시간 압박 계수 계산 (기존 로직 유지)
        project_size = context.get("project_size", "medium")
        size_multiplier = {"small": 0.9, "medium": 1.0, "large": 1.1}.get(project_size, 1.0)

        team_experience = context.get("team_experience", "intermediate")
        exp_multiplier = {"beginner": 0.8, "intermediate": 1.0, "expert": 1.2}.get(
            team_experience, 1.0
        )

        time_pressure = context.get("time_pressure", "normal")
        time_multiplier = {"low": 1.2, "normal": 1.0, "high": 0.9}.get(time_pressure, 1.0)

        adjustment_factor = size_multiplier * exp_multiplier * time_multiplier

        return {
            "auto_run_min_score": base_thresholds["auto_run_min_score"] * adjustment_factor,
            "auto_run_max_risk": base_thresholds["auto_run_max_risk"] / adjustment_factor,
            "manual_review_min_score": base_thresholds["manual_review_min_score"]
            * adjustment_factor,
            "block_threshold_score": base_thresholds["block_threshold_score"] * adjustment_factor,
        }

    async def _adjust_for_context(
        self, thresholds: dict[str, float], context: dict[str, Any]
    ) -> dict[str, float]:
        """맥락 기반 추가 임계값 조정"""
        adjusted = thresholds.copy()

        # 변경 범위, 테스트 커버리지, CI 상태에 따른 미세 조정
        change_scope = context.get("change_scope", "small")
        scope_adj = {"small": -5.0, "medium": 0.0, "large": 5.0, "breaking": 10.0}.get(
            change_scope, 0.0
        )
        adjusted["auto_run_min_score"] += scope_adj

        test_coverage = context.get("test_coverage", 80.0)
        adjusted["auto_run_min_score"] += (test_coverage - 80.0) * 0.1

        if context.get("ci_status", "passing") == "failing":
            adjusted["auto_run_min_score"] += 10.0

        return adjusted

    async def _make_intelligent_decision(
        self,
        trinity_score: float,
        risk_score: float,
        predicted_score: float,
        thresholds: dict[str, float],
        context: dict[str, Any],
    ) -> str:
        """지능형 의사결정"""
        effective_score = (trinity_score * 0.7) + (predicted_score * 0.3)
        if (
            effective_score >= thresholds["auto_run_min_score"]
            and risk_score <= thresholds["auto_run_max_risk"]
        ):
            return "AUTO_RUN"
        elif effective_score >= thresholds["manual_review_min_score"]:
            return "ASK_COMMANDER"
        elif effective_score < thresholds["block_threshold_score"]:
            return "BLOCK"
        return "ASK_COMMANDER"

    async def _calculate_confidence(self, decision: str, context: dict[str, Any]) -> float:
        """의사결정 신뢰도 계산"""
        base_confidence = 0.8
        history_size = len(self.quality_history)
        if history_size > 100:
            base_confidence += 0.1
        elif history_size < 10:
            base_confidence -= 0.2

        completeness = (
            sum(1 for k in ["project_size", "team_experience", "change_scope"] if k in context)
            / 3.0
        )
        base_confidence += (completeness - 0.5) * 0.2
        return max(0.1, min(1.0, base_confidence))

    async def _generate_recommendations(self, decision: str, context: dict[str, Any]) -> list[str]:
        """개선 권장사항 생성 (기존 로직 유지)"""
        recommendations = []
        report_lang = getattr(antigravity, "REPORT_LANGUAGE", "ko") if antigravity else "ko"

        if decision == "BLOCK":
            if report_lang == "ko":
                recommendations = [
                    "코드 품질 개선이 시급합니다",
                    "단위 테스트 추가 고려",
                    "코드 리뷰 강화 필요",
                ]
            else:
                recommendations = [
                    "Code quality improvement urgent",
                    "Consider unit tests",
                    "Strengthen code review",
                ]
        elif decision == "ASK_COMMANDER":
            if report_lang == "ko":
                recommendations = ["수동 검토 가능", "자동 수정 이슈 해결", "테스트 커버리지 개선"]
            else:
                recommendations = [
                    "Manual review possible",
                    "Fix auto-fixables",
                    "Improve coverage",
                ]
        elif decision == "AUTO_RUN":
            recommendations = ["품질 기준 만족" if report_lang == "ko" else "Quality standards met"]

        if context.get("test_coverage", 0) < 70:
            recommendations.append(
                "테스트 커버리지 70% 권장" if report_lang == "ko" else "Recommended coverage > 70%"
            )
        if not context.get("has_docs", False):
            recommendations.append(
                "문서화 개선 권장"
                if report_lang == "ko"
                else "Documentation improvement recommended"
            )

        if self.protocol_officer:
            # Formatted logic assumed handled by caller or simple return
            pass
        return recommendations

    async def _collect_learning_data(
        self, trinity_score: float, risk_score: float, context: dict[str, Any], decision: str
    ) -> None:
        """학습 데이터 수집"""
        learning_data = {
            "timestamp": datetime.now(UTC),
            "trinity_score": trinity_score,
            "risk_score": risk_score,
            "decision": decision,
            "context": context,
            "prediction_accuracy": None,
        }
        self.quality_history.append(learning_data)
        if len(self.quality_history) > 1000:
            self.quality_history = self.quality_history[-1000:]

    def _format_decision_message(self, result: dict[str, Any]) -> str:
        """결정 메시지 포맷팅"""
        # Logic extracted to Reporter but kept here as it's used by evaluate_quality_gate directly
        # TODO: Move this to Reporter too later if needed
        report_lang = getattr(antigravity, "REPORT_LANGUAGE", "ko") if antigravity else "ko"
        d, t, r, c = (
            result.get("decision"),
            result.get("trinity_score"),
            result.get("risk_score"),
            result.get("confidence"),
        )
        recs = result.get("recommendations", [])

        if report_lang == "ko":
            msg = f"품질 게이트 평가 결과:\n- 결정: {d}\n- Trinity Score: {t:.1f}\n- Risk Score: {r:.1f}\n- 신뢰도: {c:.1%}"
            if recs:
                msg += "\n\n권장사항:\n" + "\n".join(f"- {rec}" for rec in recs)
        else:
            msg = f"Quality Gate Result:\n- Decision: {d}\n- Trinity Score: {t:.1f}\n- Risk Score: {r:.1f}\n- Confidence: {c:.1%}"
            if recs:
                msg += "\n\nRecommendations:\n" + "\n".join(f"- {rec}" for rec in recs)
        return msg

    async def adapt_thresholds(self) -> dict[str, Any]:
        """동적 임계값 적응"""
        if len(self.quality_history) < 20:
            return {"status": "insufficient_data"}
        try:
            recent_decisions = self.quality_history[-50:]
            auto_runs = [d for d in recent_decisions if d["decision"] == "AUTO_RUN"]
            if auto_runs:
                success_rate = len([d for d in auto_runs if d.get("outcome") == "success"]) / len(
                    auto_runs
                )
                if success_rate > 0.95:
                    self.dynamic_thresholds["auto_run_min_score"] -= 1.0
                elif success_rate < 0.80:
                    self.dynamic_thresholds["auto_run_min_score"] += 1.0
                return {"status": "adapted", "success_rate": success_rate}
            return {"status": "adapted", "success_rate": None}
        except Exception as e:
            logger.exception(f"Threshold adaptation failed: {e}")
            return {"status": "error", "message": str(e)}

    # [Phase C] Reporting Delegation
    def generate_analysis_report(
        self, context: Any, analysis: Any, evidence: Any, next_steps: Any
    ) -> str:
        if self.reporter:
            return self.reporter.generate_analysis_report(context, analysis, evidence, next_steps)
        return "[Error] Reporter not available."

    def generate_completion_report(
        self, context: Any, analysis: Any, evidence: Any, next_steps: Any
    ) -> str | None:
        if self.reporter:
            return self.reporter.generate_completion_report(context, analysis, evidence, next_steps)
        logger.error("[Antigravity] Reporting failed: Reporter not initialized.")
        return None

    def save_report(self, report: str, filename: str) -> Path:
        if self.reporter:
            return self.reporter.save_report(report, filename)
        raise RuntimeError("Reporter not initialized.")


# 싱글톤 인스턴스
antigravity_engine = AntigravityEngine()
