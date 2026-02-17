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
# 페르소나 점수 설정 (SSOT) - HYOGOOK V5
# ═══════════════════════════════════════════════════════════════════════════════


class PersonaType(Enum):
    """페르소나 유형 (HYOGOOK V5: 仁眞善忠美)"""

    COMMANDER = "commander"
    FAMILY_HEAD = "family_head"
    CREATOR = "creator"
    JANG_YEONG_SIL = "jang_yeong_sil"  # 장영실 - 眞 (Truth)
    YI_SUN_SIN = "yi_sun_sin"  # 이순신 - 善 (Goodness)
    SHIN_SAIMDANG = "shin_saimdang"  # 신사임당 - 美 (Beauty)
    KIM_YU_SIN = "kim_yu_sin"  # 김유신 - 忠 (Loyalty)
    DEFAULT = "default"


@dataclass(frozen=True)
class PersonaScores:
    """페르소나별 기본 점수 (0-100 스케일) - HYOGOOK V5"""

    benevolence: float  # 仁 (was serenity)
    truth: float  # 眞
    goodness: float  # 善
    loyalty: float  # 忠 (was eternity)
    beauty: float  # 美


# 🏛️ 페르소나별 SSOT 점수 (HYOGOOK V5)
# 순서: benevolence(仁), truth(眞), goodness(善), loyalty(忠), beauty(美)
PERSONA_SCORE_MAP: dict[PersonaType, PersonaScores] = {
    PersonaType.COMMANDER: PersonaScores(95.0, 90.0, 85.0, 90.0, 80.0),
    PersonaType.FAMILY_HEAD: PersonaScores(90.0, 75.0, 95.0, 85.0, 85.0),
    PersonaType.CREATOR: PersonaScores(80.0, 80.0, 75.0, 75.0, 95.0),
    PersonaType.JANG_YEONG_SIL: PersonaScores(85.0, 95.0, 80.0, 90.0, 75.0),  # 眞 강조
    PersonaType.YI_SUN_SIN: PersonaScores(90.0, 80.0, 95.0, 85.0, 75.0),  # 善 강조
    PersonaType.SHIN_SAIMDANG: PersonaScores(85.0, 75.0, 80.0, 80.0, 95.0),  # 美 강조
    PersonaType.KIM_YU_SIN: PersonaScores(90.0, 80.0, 85.0, 95.0, 80.0),  # 忠 강조
    PersonaType.DEFAULT: PersonaScores(85.0, 80.0, 80.0, 80.0, 80.0),
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
        HYOGOOK V5 5덕 Raw Scores 계산 [0.0, 1.0]
        순서: benevolence, truth, goodness, loyalty, beauty

        Args:
            query_data: 쿼리 데이터 (valid_structure, risk_level, narrative 등)

        Returns:
            [benevolence, truth, goodness, loyalty, beauty] 리스트
        """
        # 1. 仁 (Benevolence): 개발자 경험 (was Serenity)
        benevolence = _get_serenity_score()

        # 2. 眞 (Truth): 구조 유효성
        truth = (
            0.0 if ("invalid" in query_data or query_data.get("valid_structure") is False) else 1.0
        )

        # 3. 善 (Goodness): 위험도 기반
        risk = query_data.get("risk_level", 0.0)
        goodness = 0.0 if risk > 0.1 else 1.0

        # 4. 忠 (Loyalty): SSOT 준수 (was Eternity)
        # 기본값으로 1.0, 세부 평가는 외부에서 주입
        loyalty = query_data.get("loyalty_score", 1.0)

        # 5. 美 (Beauty): 낟티브 품질
        narrative = query_data.get("narrative", "complete")
        beauty = 0.85 if narrative == "partial" else 1.0

        return [
            benevolence,
            truth,
            goodness,
            loyalty,
            beauty,
        ]

    def calculate_trinity_score(
        self,
        raw_scores: list[float],
        static_score: float | None = None,
    ) -> float:
        """
        HYOGOOK V5 Trinity Score 계산
        F = (In+T+G+C+B) + ⁵√(In×T×G×C×B)

        Args:
            raw_scores: 5덕 점수 [benevolence, truth, goodness, loyalty, beauty] [0.0-1.0]
            static_score: 정적 점수 (7:3 황금비 적용 시, legacy)

        Returns:
            Trinity Score (0.0-100.0)
        """
        if len(raw_scores) != 5:
            raise ValueError(f"Must have 5 raw scores, got {len(raw_scores)}")

        if not all(0.0 <= s <= 1.0 for s in raw_scores):
            raise ValueError("Raw scores must be between 0.0 and 1.0")

        # HYOGOOK V5: F = (In+T+G+C+B) + S
        benevolence, truth, goodness, loyalty, beauty = raw_scores

        # 기하평균 S (永 Eternity)
        product = benevolence * truth * goodness * loyalty * beauty
        S = product ** (1 / 5) if product > 0 else 0.0

        # 가중 산술평균
        weighted_sum = (
            benevolence * 0.25  # 仁
            + truth * 0.22  # 眞
            + goodness * 0.18  # 善
            + loyalty * 0.15  # 忠
            + beauty * 0.15  # 美
        )

        # F score (range ~6-60)
        F = weighted_sum * 10 + S  # Normalize to ~6-60 range

        # Convert to percentage (0-100)
        # F=6 → 0%, F=60 → 100%
        final_score = ((F - 6) / (60 - 6)) * 100

        if static_score is not None:
            # 7:3 황금비 적용 (legacy mode)
            final_score = (static_score * 0.7) + (final_score * 0.3)
            logger.info(
                f"[Trinity V5 7:3] Static({static_score})*0.7 + Dynamic({final_score:.1f})*0.3 = {final_score:.1f}"
            )
        else:
            logger.info(f"[Trinity V5] F={F:.2f}, S={S:.4f}, Score: {final_score:.1f}")

        return round(max(0, min(100, final_score)), 1)

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
