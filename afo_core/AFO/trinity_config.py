"""Trinity Config Management - Boot-Swap 적용"""

import os
from typing import Any

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
    THRESHOLD_VALIDATION_MAX_RISK,
    THRESHOLD_VALIDATION_MIN_TRINITY,
    WEIGHTS,
)

# SSOT BASE_CONFIG (trinity_ssot.py에서 참조)
BASE_CONFIG = {
    "weights": WEIGHTS.copy(),
    "thresholds": {
        "auto_run_trinity": int(THRESHOLD_AUTO_RUN_SCORE),
        "auto_run_risk": int(THRESHOLD_AUTO_RUN_RISK),
    },
}


def apply_learning_profile(
    base_config: dict[str, Any], profile_overrides: dict[str, Any]
) -> dict[str, Any]:
    """Learning profile overrides 적용 (선택적, 검증 후 fallback + 안전 완화 금지)"""
    effective = base_config.copy()
    effective["applied_overrides"] = []
    effective["rejected_overrides"] = []  # 안전 완화 금지로 거부된 항목들

    base_config["weights"]
    base_thresholds = base_config["thresholds"]

    # Safety 완화 금지 정책 (기본값) - 환경변수로 해제 가능
    allow_weaken_safety = os.getenv("AFO_LEARNING_ALLOW_WEAKEN_SAFETY", "0").lower() in (
        "1",
        "true",
        "yes",
    )
    effective["policy"] = {
        "allow_weaken_safety": allow_weaken_safety,
        "safety_policy": "enabled" if not allow_weaken_safety else "disabled",
    }

    # weights override (선택적)
    if "weights" in profile_overrides:
        weights_override = profile_overrides["weights"]
        # 검증: 합계 1.0, 모든 값 0-1
        if (
            isinstance(weights_override, dict)
            and abs(sum(weights_override.values()) - 1.0) < 0.001
            and all(0 <= v <= 1 for v in weights_override.values())
        ):
            effective["weights"].update(weights_override)
            effective["applied_overrides"].append("weights")

    # thresholds override (선택적 + 안전 완화 금지)
    if "thresholds" in profile_overrides:
        thresholds_override = profile_overrides["thresholds"]
        # 기본 검증 (SSOT: trinity_ssot.py)
        base_validation = (
            isinstance(thresholds_override, dict)
            and THRESHOLD_VALIDATION_MIN_TRINITY
            <= thresholds_override.get("auto_run_trinity", 90)
            <= 100
            and 0 <= thresholds_override.get("auto_run_risk", 10) <= THRESHOLD_VALIDATION_MAX_RISK
        )

        if base_validation:
            # 안전 완화 금지: 기본값보다 완화시키는 변경 거부
            new_trinity = thresholds_override.get(
                "auto_run_trinity", base_thresholds["auto_run_trinity"]
            )
            new_risk = thresholds_override.get("auto_run_risk", base_thresholds["auto_run_risk"])

            safety_weaken_detected = (
                new_trinity < base_thresholds["auto_run_trinity"]  # trinity threshold 낮춤 (완화)
                or new_risk > base_thresholds["auto_run_risk"]  # risk threshold 높임 (완화)
            )

            if safety_weaken_detected and not allow_weaken_safety:
                # 안전 완화 거부
                effective["rejected_overrides"].append(
                    {
                        "field": "thresholds",
                        "reason": "safety_weaken_forbidden",
                        "details": {
                            "base_trinity": base_thresholds["auto_run_trinity"],
                            "new_trinity": new_trinity,
                            "base_risk": base_thresholds["auto_run_risk"],
                            "new_risk": new_risk,
                        },
                    }
                )
            else:
                # 안전 완화 허용 또는 완화 없음
                effective["thresholds"].update(thresholds_override)
                effective["applied_overrides"].append("thresholds")

    return effective
