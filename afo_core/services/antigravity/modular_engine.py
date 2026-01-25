# Trinity Score: 90.0 (Established by Chancellor)
"""
Modular Antigravity Engine - 모듈식 품질 게이트 엔진
Simple Gate를 기반으로 선택적 모듈 확장
"""

import logging
from typing import Any

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
)

from .adaptive.thresholds import adaptive_thresholds
from .core.simple_gate import evaluate_gate
from .integration.protocol_officer_bridge import protocol_officer_bridge
from .ml.predictor import quality_predictor
from .reporting.reports import report_generator

logger = logging.getLogger(__name__)


class ModularAntigravityEngine:
    """
    모듈식 Antigravity 엔진
    Simple Gate를 기반으로 선택적 모듈 확장

    아키텍처 원칙:
    1. core는 외부 의존성 없음
    2. 모듈은 core만 의존 (역방향 금지)
    3. 설정으로 모듈 on/off 가능
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        모듈식 엔진 초기화
        각 모듈의 활성화 상태 설정

        Args:
            config: 모듈 활성화 설정
        """
        self.config = config or self._get_default_config()
        self._validate_config()

        logger.info("✅ Modular Antigravity Engine 초기화 완료")
        logger.info(f"활성화 모듈: {self._get_active_modules()}")

    def _get_default_config(self) -> dict[str, Any]:
        """기본 설정 반환"""
        return {
            "use_ml_prediction": False,  # ML 예측 사용
            "use_adaptive_thresholds": False,  # 동적 임계값 사용
            "use_protocol_officer": False,  # Protocol Officer 사용
            "use_reporting": False,  # 보고서 생성 사용
        }

    def _validate_config(self) -> None:
        """설정 유효성 검증"""
        required_keys = [
            "use_ml_prediction",
            "use_adaptive_thresholds",
            "use_protocol_officer",
            "use_reporting",
        ]

        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"필수 설정 누락: {key}")

    def _get_active_modules(self) -> list[str]:
        """활성화된 모듈 목록 반환"""
        active = []
        if self.config["use_ml_prediction"]:
            active.append("ML Prediction")
        if self.config["use_adaptive_thresholds"]:
            active.append("Adaptive Thresholds")
        if self.config["use_protocol_officer"]:
            active.append("Protocol Officer")
        if self.config["use_reporting"]:
            active.append("Reporting")
        return active

    async def evaluate_quality_gate(
        self,
        trinity_score: float,
        risk_score: float,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        모듈식 품질 게이트 평가
        Simple Gate를 기반으로 선택적 모듈 적용

        Args:
            trinity_score: Trinity Score (0-100)
            risk_score: Risk Score (0-100)
            context: 평가 맥락 (선택적)

        Returns:
            평가 결과
        """
        context = context or {}

        # 1. 기본 판정 (항상 실행)
        decision = evaluate_gate(trinity_score, risk_score)

        # 2. ML 예측 적용 (선택적)
        predicted_score = trinity_score
        if self.config["use_ml_prediction"]:
            try:
                predicted_score = quality_predictor.predict_future_quality(trinity_score, context)
                quality_predictor.collect_learning_data(
                    trinity_score, risk_score, context, decision
                )
            except Exception as e:
                logger.warning(f"ML 예측 실패, 기본값 사용: {e}")

        # 3. 동적 임계값 적용 (선택적, SSOT: trinity_ssot.py)
        thresholds = {
            "auto_run_min_score": THRESHOLD_AUTO_RUN_SCORE,
            "auto_run_max_risk": THRESHOLD_AUTO_RUN_RISK,
        }
        if self.config["use_adaptive_thresholds"]:
            try:
                thresholds = adaptive_thresholds.calculate_dynamic_thresholds(context)
                thresholds = adaptive_thresholds.adjust_for_context(thresholds, context)
            except Exception as e:
                logger.warning(f"동적 임계값 계산 실패, 기본값 사용: {e}")

        # 4. 향상된 판정 (ML 예측 반영)
        if self.config["use_ml_prediction"]:
            effective_score = (trinity_score * 0.7) + (predicted_score * 0.3)
            if (
                effective_score >= thresholds["auto_run_min_score"]
                and risk_score <= thresholds["auto_run_max_risk"]
            ):
                decision = "AUTO_RUN"
            else:
                decision = "ASK_COMMANDER"

        # 5. 결과 구성
        result = {
            "decision": decision,
            "trinity_score": trinity_score,
            "risk_score": risk_score,
            "predicted_score": (predicted_score if self.config["use_ml_prediction"] else None),
            "dynamic_thresholds": (thresholds if self.config["use_adaptive_thresholds"] else None),
            "confidence": 0.8,  # 기본 신뢰도
            "active_modules": self._get_active_modules(),
        }

        if self.config["use_protocol_officer"]:
            try:
                formatted_message: str = protocol_officer_bridge.format_decision_message(result)
                result["formatted_message"] = formatted_message  # type: ignore[assignment]
            except Exception as e:
                logger.warning(f"Protocol Officer 포맷팅 실패: {e}")

        return result

    async def generate_report(
        self,
        report_type: str,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str | None:
        """
        보고서 생성 (선택적 모듈)

        Args:
            report_type: "analysis" 또는 "completion"
            context: 보고서 맥락
            analysis: 분석 결과
            evidence: 증거 데이터
            next_steps: 다음 단계

        Returns:
            생성된 보고서 또는 None
        """
        if not self.config["use_reporting"]:
            logger.info("보고서 모듈 비활성화")
            return None

        try:
            if report_type == "analysis":
                return report_generator.generate_analysis_report(
                    context, analysis, evidence, next_steps
                )
            elif report_type == "completion":
                return report_generator.generate_completion_report(
                    context, analysis, evidence, next_steps
                )
            else:
                raise ValueError(f"지원하지 않는 보고서 타입: {report_type}")

        except Exception as e:
            logger.error(f"보고서 생성 실패: {e}")
            return None

    def save_report(self, report: str, filename: str) -> str | None:
        """
        보고서 저장 (선택적 모듈)

        Args:
            report: 보고서 내용
            filename: 파일명

        Returns:
            저장된 파일 경로 또는 None
        """
        if not self.config["use_reporting"]:
            logger.info("보고서 모듈 비활성화")
            return None

        try:
            saved_path = report_generator.save_report(report, filename)
            return str(saved_path)
        except Exception as e:
            logger.error(f"보고서 저장 실패: {e}")
            return None

    async def adapt_thresholds(self) -> dict[str, Any]:
        """
        임계값 적응 (선택적 모듈)

        Returns:
            적응 결과
        """
        if not self.config["use_adaptive_thresholds"]:
            return {"status": "module_disabled"}

        try:
            # 실제로는 quality_predictor의 히스토리를 사용해야 함
            # 여기서는 모의 데이터 사용
            mock_history: list[dict[str, Any]] = []
            return adaptive_thresholds.adapt_thresholds(mock_history)
        except Exception as e:
            logger.error(f"임계값 적응 실패: {e}")
            return {"status": "error", "message": str(e)}


# 설정 기반 팩토리 함수들
def create_simple_engine() -> ModularAntigravityEngine:
    """단순 엔진 생성 (코어만 활성화)"""
    config = {
        "use_ml_prediction": False,
        "use_adaptive_thresholds": False,
        "use_protocol_officer": False,
        "use_reporting": False,
    }
    return ModularAntigravityEngine(config)


def create_full_engine() -> ModularAntigravityEngine:
    """완전 엔진 생성 (모든 모듈 활성화)"""
    config = {
        "use_ml_prediction": True,
        "use_adaptive_thresholds": True,
        "use_protocol_officer": True,
        "use_reporting": True,
    }
    return ModularAntigravityEngine(config)


def create_custom_engine(
    use_ml: bool = False,
    use_adaptive: bool = False,
    use_protocol: bool = False,
    use_reporting: bool = False,
) -> ModularAntigravityEngine:
    """커스텀 엔진 생성"""
    config = {
        "use_ml_prediction": use_ml,
        "use_adaptive_thresholds": use_adaptive,
        "use_protocol_officer": use_protocol,
        "use_reporting": use_reporting,
    }
    return ModularAntigravityEngine(config)


# 기본 인스턴스들
simple_engine = create_simple_engine()
full_engine = create_full_engine()
