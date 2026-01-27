# Trinity Score: 90.0 (Established by Chancellor)
"""
Trinity Score Calculator (SSOT)
동적 Trinity Score 계산기 - SSOT 가중치 기반 정밀 산출

리팩터링: 도메인 레이어(TrinityMetrics) 활용, 중복 제거
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from AFO.domain.metrics.trinity import TrinityInputs, TrinityMetrics

try:
    from AFO.utils.trinity_type_validator import validate_with_trinity
except ImportError:

    def validate_with_trinity[TF: Callable[..., Any]](func: TF) -> TF:
        """Fallback decorator when trinity_type_validator is not available."""
        return func


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 페르소나 점수 설정 (SSOT)
# ═══════════════════════════════════════════════════════════════════════════════


class PersonaType(Enum):
    """페르소나 유형 (眞善美 3략사 + 시스템 역할)"""

    COMMANDER = "commander"
    FAMILY_HEAD = "family_head"
    CREATOR = "creator"
    JANG_YEONG_SIL = "jang_yeong_sil"  # 제갈량 - 眞 (Truth)
    YI_SUN_SIN = "yi_sun_sin"  # 사마의 - 善 (Goodness)
    SHIN_SAIMDANG = "shin_saimdang"  # 주유 - 美 (Beauty)
    DEFAULT = "default"


@dataclass(frozen=True)
class PersonaScores:
    """페르소나별 기본 점수 (0-100 스케일)"""

    truth: float
    goodness: float
    beauty: float
    serenity: float
    eternity: float


# 🏛️ 페르소나별 SSOT 점수 (하드코딩 대신 설정으로 분리)
PERSONA_SCORE_MAP: dict[PersonaType, PersonaScores] = {
    PersonaType.COMMANDER: PersonaScores(90.0, 85.0, 80.0, 95.0, 90.0),
    PersonaType.FAMILY_HEAD: PersonaScores(75.0, 95.0, 85.0, 90.0, 85.0),
    PersonaType.CREATOR: PersonaScores(80.0, 75.0, 95.0, 80.0, 75.0),
    PersonaType.JANG_YEONG_SIL: PersonaScores(95.0, 80.0, 75.0, 85.0, 90.0),  # 眞 강조
    PersonaType.YI_SUN_SIN: PersonaScores(80.0, 95.0, 75.0, 90.0, 85.0),  # 善 강조
    PersonaType.SHIN_SAIMDANG: PersonaScores(75.0, 80.0, 95.0, 85.0, 80.0),  # 美 강조
    PersonaType.DEFAULT: PersonaScores(80.0, 80.0, 80.0, 85.0, 80.0),
}


def _resolve_persona_type(persona_data: dict[str, Any]) -> PersonaType:
    """페르소나 데이터에서 PersonaType 결정"""
    persona_id = persona_data.get("type", persona_data.get("id", ""))
    role = persona_data.get("role", "").lower()

    # 직접 매칭
    try:
        return PersonaType(persona_id)
    except ValueError:
        pass

    # 역할 기반 매칭
    if "truth" in role or "strategist" in role:
        return PersonaType.JANG_YEONG_SIL
    if "goodness" in role or "guardian" in role:
        return PersonaType.YI_SUN_SIN
    if "beauty" in role or "architect" in role:
        return PersonaType.SHIN_SAIMDANG

    return PersonaType.DEFAULT


# ═══════════════════════════════════════════════════════════════════════════════
# Serenity (Friction) 계산 지원
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class SerenityMetrics:
    """Serenity 메트릭 (Friction Calibrator 호환)"""

    score: float = 92.0  # 0-100 스케일


def _get_serenity_score() -> float:
    """FrictionCalibrator에서 Serenity 점수 조회 (0.0-1.0)"""
    try:
        from config.friction_calibrator import friction_calibrator

        metrics = friction_calibrator.calculate_serenity()
        return metrics.score / 100.0
    except ImportError:
        return SerenityMetrics().score / 100.0


# ═══════════════════════════════════════════════════════════════════════════════
# Trinity Calculator (핵심 클래스)
# ═══════════════════════════════════════════════════════════════════════════════


class TrinityCalculator:
    """
    Trinity Score Calculator (SSOT Implementation)

    도메인 레이어(TrinityMetrics)를 활용하여 5기둥 점수 계산
    """

    @validate_with_trinity
    def calculate_raw_scores(self, query_data: dict[str, Any]) -> list[float]:
        """
        5기둥 Raw Scores 계산 [0.0, 1.0]

        Args:
            query_data: 쿼리 데이터 (valid_structure, risk_level, narrative 등)

        Returns:
            [truth, goodness, beauty, serenity, eternity] 리스트
        """
        # 1. 眞 (Truth): 구조 유효성
        truth = (
            0.0 if ("invalid" in query_data or query_data.get("valid_structure") is False) else 1.0
        )

        # 2. 善 (Goodness): 위험도 기반
        risk = query_data.get("risk_level", 0.0)
        goodness = 0.0 if risk > 0.1 else 1.0

        # 3. 美 (Beauty): 내러티브 품질
        narrative = query_data.get("narrative", "complete")
        beauty = 0.85 if narrative == "partial" else 1.0

        # 4. 孝 (Serenity): Friction Calibrator 연동
        serenity = _get_serenity_score()

        # 5. 永 (Eternity): 기본값
        eternity = 1.0

        # TrinityInputs로 검증 (clamp 적용)
        validated = TrinityInputs(
            truth=truth, goodness=goodness, beauty=beauty, filial_serenity=serenity
        )

        return [
            validated.truth,
            validated.goodness,
            validated.beauty,
            validated.filial_serenity,
            eternity,
        ]

    def calculate_trinity_score(
        self,
        raw_scores: list[float],
        static_score: float | None = None,
    ) -> float:
        """
        Trinity Score 계산 (도메인 레이어 활용)

        Args:
            raw_scores: 5기둥 점수 [0.0-1.0]
            static_score: 정적 점수 (7:3 황금비 적용 시)

        Returns:
            Trinity Score (0.0-100.0)
        """
        if len(raw_scores) != 5:
            raise ValueError(f"Must have 5 raw scores, got {len(raw_scores)}")

        if not all(0.0 <= s <= 1.0 for s in raw_scores):
            raise ValueError("Raw scores must be between 0.0 and 1.0")

        # 도메인 레이어로 계산
        inputs = TrinityInputs(
            truth=raw_scores[0],
            goodness=raw_scores[1],
            beauty=raw_scores[2],
            filial_serenity=raw_scores[3],
        )
        metrics = TrinityMetrics.from_inputs(inputs, eternity=raw_scores[4])

        # 0.0-1.0 → 0-100 스케일
        dynamic_score = metrics.trinity_score * 100

        if static_score is not None:
            # 7:3 황금비 적용
            final_score = (static_score * 0.7) + (dynamic_score * 0.3)
            logger.info(
                f"[Trinity 7:3] Static({static_score})*0.7 + Dynamic({dynamic_score:.1f})*0.3 = {final_score:.1f}"
            )
        else:
            final_score = dynamic_score
            logger.info(f"[TrinityCalculator] Raw: {raw_scores} -> Score: {final_score:.1f}")

        return round(final_score, 1)

    def calculate_metrics(self, query_data: dict[str, Any]) -> TrinityMetrics:
        """
        전체 TrinityMetrics 객체 반환 (확장 API)

        Args:
            query_data: 쿼리 데이터

        Returns:
            TrinityMetrics (serenity_core, balance_delta 등 포함)
        """
        raw_scores = self.calculate_raw_scores(query_data)
        inputs = TrinityInputs(
            truth=raw_scores[0],
            goodness=raw_scores[1],
            beauty=raw_scores[2],
            filial_serenity=raw_scores[3],
        )
        return TrinityMetrics.from_inputs(inputs, eternity=raw_scores[4])

    async def calculate_persona_scores(
        self,
        persona_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        """
        페르소나 기반 Trinity Score 계산

        Args:
            persona_data: 페르소나 데이터 (id, name, type, role 등)
            context: 추가 맥락 정보 (boost 등)

        Returns:
            5기둥 점수 딕셔너리
        """
        persona_type = _resolve_persona_type(persona_data)
        base_scores = PERSONA_SCORE_MAP[persona_type]

        scores = [
            base_scores.truth,
            base_scores.goodness,
            base_scores.beauty,
            base_scores.serenity,
            base_scores.eternity,
        ]

        # 컨텍스트 부스트 적용
        if context and (boost := context.get("boost", 0.0)):
            scores = [min(100.0, s + boost) for s in scores]

        # Prometheus 메트릭 기록
        self._record_prometheus_metrics(scores)

        return {
            "truth": scores[0],
            "goodness": scores[1],
            "beauty": scores[2],
            "serenity": scores[3],
            "eternity": scores[4],
        }

    @staticmethod
    def _record_prometheus_metrics(scores: list[float]) -> None:
        """Prometheus 메트릭 기록 (선택적)"""
        try:
            from AFO.api.middleware.prometheus import record_trinity_score

            pillars = ["truth", "goodness", "beauty", "serenity", "eternity"]
            for pillar, score in zip(pillars, scores, strict=True):
                record_trinity_score(pillar, score)
        except ImportError:
            logger.debug("Prometheus middleware not available")


# ═══════════════════════════════════════════════════════════════════════════════
# 싱글톤 & 호환성 함수
# ═══════════════════════════════════════════════════════════════════════════════

trinity_calculator = TrinityCalculator()


@dataclass
class TrinityResult:
    """DSPy 호환 결과 객체"""

    overall: float


def calculate_trinity_score(pred_str: str, gt_str: str) -> TrinityResult:
    """
    DSPy optimizer 호환 함수 (문자열 유사도 기반)

    Args:
        pred_str: 예측 문자열
        gt_str: 정답 문자열

    Returns:
        TrinityResult with overall score (0-100)
    """
    pred_words = set(pred_str.lower().split())
    gt_words = set(gt_str.lower().split())

    if not gt_words:
        similarity = 1.0 if not pred_words else 0.0
    else:
        intersection = pred_words & gt_words
        similarity = len(intersection) / len(gt_words)

    return TrinityResult(overall=similarity * 100)
