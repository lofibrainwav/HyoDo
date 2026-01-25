# Trinity Score: 90.0 (Established by Chancellor)
"""Chancellor Graph Rule Constants (SSOT)

All decision rules used by the Chancellor Graph for AUTO_RUN/ASK routing.
These constants ensure consistency across all nodes and provide audit trails.
"""

import hashlib
from typing import Final, Literal

# 🏛️ SSOT Trinity Weights - Re-export from canonical source
from AFO.domain.metrics.trinity_ssot import WEIGHTS


# 🛡️ SSOT 런타임 가드: 가중치 검증 함수
def validate_weights(weights: dict[str, float]) -> None:
    """SSOT 무결성 검증: 가중치 합계가 정확히 1.0인지 확인
    SSOT 드리프트 방지를 위한 런타임 가드
    """
    total = sum(float(v) for v in weights.values())
    if abs(total - 1.0) > 1e-6:  # 부동소수점 오차 고려
        raise ValueError(
            f"SSOT VIOLATION: WEIGHTS sum is {total:.6f}, must be 1.0. "
            f"SSOT drift detected in {weights}"
        )


# 🔐 SSOT 해시 스탬프: 변경 감지용 (SHA256 12자리)
WEIGHTS_HASH = hashlib.sha256(str(sorted(WEIGHTS.items())).encode()).hexdigest()[:12]

# 런타임 SSOT 검증 실행 (무조건)
validate_weights(WEIGHTS)

# Rule IDs for Chancellor Graph decision making
RULE_DRY_RUN_OVERRIDE: Final = "R1_DRY_RUN_OVERRIDE"
RULE_RESIDUAL_DOUBT: Final = "R2_RESIDUAL_DOUBT"
RULE_VETO_LOW_PILLARS: Final = "R3_VETO_LOW_PILLARS"
RULE_AUTORUN_THRESHOLD: Final = "R4_AUTORUN_THRESHOLD"
RULE_FALLBACK_ASK: Final = "R5_FALLBACK_ASK"

# Type alias for valid rule IDs
RuleId = Literal[
    "R1_DRY_RUN_OVERRIDE",
    "R2_RESIDUAL_DOUBT",
    "R3_VETO_LOW_PILLARS",
    "R4_AUTORUN_THRESHOLD",
    "R5_FALLBACK_ASK",
]

# Rule descriptions for documentation and debugging
RULE_DESCRIPTIONS: dict[RuleId, str] = {
    RULE_DRY_RUN_OVERRIDE: "Global DRY_RUN_DEFAULT flag overrides all decisions",
    RULE_RESIDUAL_DOUBT: "High uncertainty or incomplete pillar assessment",
    RULE_VETO_LOW_PILLARS: "Any pillar score below minimum threshold vetoes AUTO_RUN",
    RULE_AUTORUN_THRESHOLD: "Trinity Score >= 90 AND Risk Score <= 10 enables AUTO_RUN",
    RULE_FALLBACK_ASK: "Default fallback to ASK_COMMANDER for all other cases",
}

# Export all rule constants
__all__ = [
    "RULE_AUTORUN_THRESHOLD",
    "RULE_DESCRIPTIONS",
    "RULE_DRY_RUN_OVERRIDE",
    "RULE_FALLBACK_ASK",
    "RULE_RESIDUAL_DOUBT",
    "RULE_VETO_LOW_PILLARS",
    "WEIGHTS",
    "WEIGHTS_HASH",
    "RuleId",
    "validate_weights",
]
