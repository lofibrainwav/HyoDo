# Trinity Score SSOT - Aligned with TRINITY_OS_PERSONAS.yaml v3 (2025-12-21)
"""[TRUTH WIRING]
Trinity Pillar SSOT (Single Source of Truth)
Defines the immutable weights for the 5 Pillars of the AFO Kingdom.
This file must be treated as a constant law.

⚠️ WARNING: These weights MUST match TRINITY_OS_PERSONAS.yaml exactly.
   Trinity = 헌법 (Constitution), Friction = 도구 (Tool) - 분리 운영 필수!
"""

from typing import Final

# 🏛️ SSOT Trinity Weights (眞善美孝永) - TRINITY_OS_PERSONAS.yaml v3 정본
# Formula: 0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永 = 1.00
WEIGHTS = {
    "truth": 0.35,  # 眞: 장영실 (Technical Certainty)
    "goodness": 0.35,  # 善: 이순신 (Ethical Safety)
    "beauty": 0.20,  # 美: 신사임당 (UX/Aesthetics)
    "serenity": 0.08,  # 孝: 승상 (Filial Serenity)
    "eternity": 0.02,  # 永: 승상 (Eternal Legacy)
}

# 🏛️ 5 Pillar Weights (Total: 1.0) - SSOT Canonical Values
WEIGHT_TRUTH: Final[float] = 0.35
WEIGHT_GOODNESS: Final[float] = 0.35
WEIGHT_BEAUTY: Final[float] = 0.20
WEIGHT_SERENITY: Final[float] = 0.08
WEIGHT_ETERNITY: Final[float] = 0.02

# 🛡️ Governance Thresholds - AUTO_RUN (Trinity >= 90 AND Risk <= 10)
THRESHOLD_AUTO_RUN_SCORE: Final[float] = 90.0
THRESHOLD_AUTO_RUN_RISK: Final[float] = 10.0

# 🛡️ Governance Thresholds - ASK_COMMANDER (Trinity >= 75 AND Risk <= 25)
THRESHOLD_ASK_TRINITY: Final[float] = 75.0
THRESHOLD_ASK_RISK: Final[float] = 25.0

# ⚖️ Balance Thresholds - 5기둥 균형 판정
THRESHOLD_BALANCE_WARNING: Final[float] = 0.30  # Δ < 0.30 = balanced
THRESHOLD_BALANCE_IMBALANCED: Final[float] = 0.50  # Δ >= 0.50 = imbalanced

# 🔒 Validation Thresholds - Learning Profile 검증 범위
THRESHOLD_VALIDATION_MIN_TRINITY: Final[int] = 80  # 최소 허용 Trinity 임계값
THRESHOLD_VALIDATION_MAX_RISK: Final[int] = 20  # 최대 허용 Risk 임계값

# 🌉 System Constants
DEFAULT_HEARTBEAT: Final[int] = 68


class TrinityWeights:
    """[Compatibility Layer]
    Namespace for Trinity Weights to match usage in trinity.py
    SSOT: TRINITY_OS_PERSONAS.yaml v3
    """

    TRUTH = WEIGHT_TRUTH
    GOODNESS = WEIGHT_GOODNESS
    BEAUTY = WEIGHT_BEAUTY
    SERENITY = WEIGHT_SERENITY
    ETERNITY = WEIGHT_ETERNITY


class GovernanceThresholds:
    """[Compatibility Layer]
    Namespace for Governance Thresholds used in Chancellor Graph
    SSOT: AGENTS.md Rule #1
    """

    AUTO_RUN_TRINITY = THRESHOLD_AUTO_RUN_SCORE
    AUTO_RUN_RISK = THRESHOLD_AUTO_RUN_RISK
    ASK_TRINITY = THRESHOLD_ASK_TRINITY
    ASK_RISK = THRESHOLD_ASK_RISK
