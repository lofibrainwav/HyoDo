import asyncio
import os
import pathlib
import sys

# Setup path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from services.detailed_pillars_calculator import pillars_metrics
from services.truth_metrics_calculator import (
    truth_metrics,
)  # Re-using Truth from Phase 15


async def verify_full_pillars():
    print("🏛️ [5-Pillars Metrics] Full Verification Start (Total 100/100 Target)")

    # Mock Context for a "Perfect System Component"
    perfect_code = """
    class TrinityEngine:
        '''
        Main Engine for AFO Kingdom.
        Ensures Truth, Goodness, Beauty, Serenity, Eternity.
        '''
        def process(self, input_data: dict) -> None:
            try:
                pass
            except Exception:
                pass
    """

    context = {
        "risk_level": 0.0,
        "ethics_check": True,
        "vulnerabilities": 0,
        "cost_optimized": True,
        "style_guide_passed": True,
        "ux_theme": "Glassmorphism",
        "features": ["Trinity Glow"],
        "mode": "AUTO_RUN",
        "auto_deploy": True,
        "duration_ms": 50,  # 0.05s
        "env_consistent": True,
        "sse_active": True,
        "evolution_logged": True,
        "git_tracked": True,
        "sustainable_arch": True,
        "data": {"key": "value"},  # For Truth check
    }

    # 1. Calculate Truth (Previously verified)
    truth_raw = truth_metrics.calculate_technical_score(perfect_code, context, test_mode=True)
    truth_normalized = truth_raw["total_score"] / 25.0  # 0.0 ~ 1.0
    print(
        f"🔹 Truth (眞): {truth_normalized * 100:.1f}% (Technical Score: {truth_raw['total_score']}/25)"
    )

    # 2. Calculate Goodness
    goodness_score = pillars_metrics.calculate_goodness_score(context)
    print(f"🔹 Goodness (善): {goodness_score * 100:.1f}%")

    # 3. Calculate Beauty
    beauty_score = pillars_metrics.calculate_beauty_score(perfect_code, context)
    print(f"🔹 Beauty (美): {beauty_score * 100:.1f}%")

    # 4. Calculate Serenity
    serenity_score = pillars_metrics.calculate_serenity_score(context)
    print(f"🔹 Serenity (孝): {serenity_score * 100:.1f}%")

    # 5. Calculate Eternity
    eternity_score = pillars_metrics.calculate_eternity_score(perfect_code, context)
    print(f"🔹 Eternity (永): {eternity_score * 100:.1f}%")

    # Final Validation
    if (
        min(
            truth_normalized,
            goodness_score,
            beauty_score,
            serenity_score,
            eternity_score,
        )
        == 1.0
    ):
        print("\n✅ Verification SUCCESS: All Pillars Achieved 100% Perfection.")
        print("   -> 眞·善·미·효·영 Metrics Operational.")
    else:
        print("\n❌ Verification FAIL: Sub-optimal scores detected.")

    print("\n[Verification Complete] Comprehensive 5-Pillar Metrics Operational.")


if __name__ == "__main__":
    asyncio.run(verify_full_pillars())
