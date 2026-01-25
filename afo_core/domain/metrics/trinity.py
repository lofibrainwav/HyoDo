from __future__ import annotations

from dataclasses import dataclass
from math import isclose, prod
from typing import Any, Literal

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_BALANCE_IMBALANCED,
    THRESHOLD_BALANCE_WARNING,
    TrinityWeights,
)

#!/usr/bin/env python3
"""
AFO Trinity Metrics Calculator

眞善美孝 (Truth, Goodness, Beauty, Filial Serenity) 수학 공식 구현

핵심 공식:
1. Serenity(§) = ∛(T × G × B) - 기하평균
2. Trinity Score = (T + G + B + H) / 4 - 산술평균
3. ΔTrinity = Max - Min - 균형 체크

眞善美孝: 眞(안전) 善(점진) 美(구조) 孝(자동화)
"""


@dataclass(frozen=True)
class TrinityInputs:
    """眞善美孝 4기둥 입력값 (0.0 ~ 1.0)

    Attributes:
        truth: 眞 (Truth) - 기술적 확실성
        goodness: 善 (Goodness) - 인간 중심, 윤리·안정성
        beauty: 美 (Beauty) - 단순함·우아함
        filial_serenity: 孝 (Filial Serenity) - 평온 수호, 연속성

    """

    truth: float
    goodness: float
    beauty: float
    filial_serenity: float

    def __post_init__(self) -> None:
        """Validate an auto-clamp values to 0.0-1.0 range (Serenity Logic)"""
        # Since frozen=True, we must use object.__setattr__
        object.__setattr__(self, "truth", self._clamp(self.truth))
        object.__setattr__(self, "goodness", self._clamp(self.goodness))
        object.__setattr__(self, "beauty", self._clamp(self.beauty))
        object.__setattr__(self, "filial_serenity", self._clamp(self.filial_serenity))

    @staticmethod
    def _clamp(value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def to_100_scale(self) -> TrinityInputs:
        """100점 스케일로 변환 (0~100)"""
        try:
            return TrinityInputs(
                truth=self.truth * 100,
                goodness=self.goodness * 100,
                beauty=self.beauty * 100,
                filial_serenity=self.filial_serenity * 100,
            )
        except Exception:
            return TrinityInputs(0, 0, 0, 0)

    @classmethod
    def from_100_scale(
        cls, truth: float, goodness: float, beauty: float, filial_serenity: float
    ) -> TrinityInputs:
        """100점 스케일에서 생성"""
        try:
            return cls(
                truth=truth / 100.0,
                goodness=goodness / 100.0,
                beauty=beauty / 100.0,
                filial_serenity=filial_serenity / 100.0,
            )
        except Exception:
            return cls(0, 0, 0, 0)


@dataclass
class TrinityMetrics:
    """眞善美孝永 5기둥 메트릭 계산 결과 (SSOT: TRINITY_OS_PERSONAS.yaml)

    Attributes:
        truth: 眞 점수 (35% 가중치)
        goodness: 善 점수 (35% 가중치)
        beauty: 美 점수 (20% 가중치)
        filial_serenity: 孝 점수 (8% 가중치)
        eternity: 永 점수 (2% 가중치)
        serenity_core: Serenity(§) = ∛(T × G × B) - 기하평균
        trinity_score: Trinity Score = 가중 합 (0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永)
        balance_delta: ΔTrinity = Max - Min
        balance_status: 균형 상태 ("balanced" | "warning" | "imbalanced")

    """

    # SSOT 가중치 (TRINITY_OS_PERSONAS.yaml -> trinity_ssot.py)
    WEIGHT_TRUTH = TrinityWeights.TRUTH
    WEIGHT_GOODNESS = TrinityWeights.GOODNESS
    WEIGHT_BEAUTY = TrinityWeights.BEAUTY
    WEIGHT_SERENITY = TrinityWeights.SERENITY
    WEIGHT_ETERNITY = TrinityWeights.ETERNITY

    truth: float
    goodness: float
    beauty: float
    filial_serenity: float
    eternity: float  # 永 - 영속성
    serenity_core: float  # S = geometric mean of T, G, B
    trinity_score: float  # weighted sum
    balance_delta: float  # max - min
    balance_status: Literal["balanced", "warning", "imbalanced"]

    @classmethod
    def from_inputs(cls, inputs: TrinityInputs, eternity: float = 1.0) -> TrinityMetrics:
        """입력값으로부터 Trinity 메트릭 계산 (5기둥 SSOT 가중치)"""
        try:
            x = inputs
            e = max(0.0, min(1.0, eternity))  # clamp eternity

            t = x.truth
            g = x.goodness
            b = x.beauty
            h = x.filial_serenity

            # Serenity core: geometric mean of T, G, B
            if (
                isclose(t, 0.0, abs_tol=1e-9)
                or isclose(g, 0.0, abs_tol=1e-9)
                or isclose(b, 0.0, abs_tol=1e-9)
            ):
                serenity_core = 0.0
            else:
                serenity_core = prod([t, g, b]) ** (1.0 / 3.0)

            # Trinity Score: SSOT 가중 합 (0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永)
            trinity_score = (
                cls.WEIGHT_TRUTH * t
                + cls.WEIGHT_GOODNESS * g
                + cls.WEIGHT_BEAUTY * b
                + cls.WEIGHT_SERENITY * h
                + cls.WEIGHT_ETERNITY * e
            )

            # Balance delta: 5기둥 max - min
            values = [t, g, b, h, e]
            balance_delta = max(values) - min(values)

            # Balance status (SSOT: trinity_ssot.py)
            if balance_delta < THRESHOLD_BALANCE_WARNING:
                balance_status: Literal["balanced", "warning", "imbalanced"] = "balanced"
            elif balance_delta < THRESHOLD_BALANCE_IMBALANCED:
                balance_status = "warning"
            else:
                balance_status = "imbalanced"

            return cls(
                truth=t,
                goodness=g,
                beauty=b,
                filial_serenity=h,
                eternity=e,
                serenity_core=serenity_core,
                trinity_score=trinity_score,
                balance_delta=balance_delta,
                balance_status=balance_status,
            )
        except Exception:
            return cls(0, 0, 0, 0, 0, 0, 0, 0, "imbalanced")

    def to_100_scale(self) -> TrinityMetrics:
        """100점 스케일로 변환"""
        try:
            return TrinityMetrics(
                truth=self.truth * 100,
                goodness=self.goodness * 100,
                beauty=self.beauty * 100,
                filial_serenity=self.filial_serenity * 100,
                eternity=self.eternity * 100,
                serenity_core=self.serenity_core * 100,
                trinity_score=self.trinity_score * 100,
                balance_delta=self.balance_delta * 100,
                balance_status=self.balance_status,
            )
        except Exception:
            return self

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (API 응답용) - 5기둥 SSOT"""
        try:
            return {
                "truth": round(self.truth, 4),
                "goodness": round(self.goodness, 4),
                "beauty": round(self.beauty, 4),
                "filial_serenity": round(self.filial_serenity, 4),
                "eternity": round(self.eternity, 4),
                "serenity_core": round(self.serenity_core, 4),
                "trinity_score": round(self.trinity_score, 4),
                "balance_delta": round(self.balance_delta, 4),
                "balance_status": self.balance_status,
                "weights": {
                    "truth": self.WEIGHT_TRUTH,
                    "goodness": self.WEIGHT_GOODNESS,
                    "beauty": self.WEIGHT_BEAUTY,
                    "filial_serenity": self.WEIGHT_SERENITY,
                    "eternity": self.WEIGHT_ETERNITY,
                },
            }
        except Exception:
            return {"error": "failed to convert to dict"}

    def __str__(self) -> str:
        """문자열 표현 - 5기둥 SSOT"""
        try:
            return (
                f"TrinityMetrics(\n"
                f"  眞 (Truth 35%): {self.truth:.3f}\n"
                f"  善 (Goodness 35%): {self.goodness:.3f}\n"
                f"  美 (Beauty 20%): {self.beauty:.3f}\n"
                f"  孝 (Serenity 8%): {self.filial_serenity:.3f}\n"
                f"  永 (Eternity 2%): {self.eternity:.3f}\n"
                f"  Serenity(§): {self.serenity_core:.3f}\n"
                f"  Trinity Score: {self.trinity_score:.3f}\n"
                f"  ΔTrinity: {self.balance_delta:.3f} ({self.balance_status})\n"
                f")"
            )
        except Exception:
            return "TrinityMetrics(Error)"


def calculate_trinity(
    truth: float,
    goodness: float,
    beauty: float,
    filial_serenity: float,
    eternity: float = 1.0,
    from_100_scale: bool = False,
) -> TrinityMetrics:
    """Trinity 메트릭 계산 헬퍼 함수 (5기둥 SSOT 가중치)"""
    try:
        if from_100_scale:
            inputs = TrinityInputs.from_100_scale(truth, goodness, beauty, filial_serenity)
            eternity_normalized = eternity / 100.0
        else:
            inputs = TrinityInputs(
                truth=truth,
                goodness=goodness,
                beauty=beauty,
                filial_serenity=filial_serenity,
            )
            eternity_normalized = eternity

        return TrinityMetrics.from_inputs(inputs, eternity=eternity_normalized)
    except Exception:
        return TrinityMetrics(0, 0, 0, 0, 0, 0, 0, 0, "imbalanced")


# 예시 사용법
if __name__ == "__main__":
    # 0~1 스케일 예시 (5기둥)
    inputs = TrinityInputs(truth=0.95, goodness=0.90, beauty=0.85, filial_serenity=1.0)
    metrics = TrinityMetrics.from_inputs(inputs, eternity=1.0)
    print(metrics)
    print(f"\n가중치 합계: {0.35 + 0.35 + 0.20 + 0.08 + 0.02} = 1.00")

    # 100점 스케일 예시
    metrics_100 = calculate_trinity(95, 90, 85, 100, 100, from_100_scale=True)
    print("\n100점 스케일:")
    print(metrics_100.to_100_scale())
