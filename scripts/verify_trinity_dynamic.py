import os
import pathlib
import sys

sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.domain.metrics.trinity_manager import trinity_manager


def verify_trinity_dynamic() -> None:
    print("=== Dynamic Trinity Score Verification ===")

    # 1. Initial State
    initial = trinity_manager.get_current_metrics()
    print(f"\n[Initial State] Score: {initial.trinity_score:.4f}")
    if initial.trinity_score == 1.0:
        print("✅ Initial Score is Perfect (1.0)")
    else:
        print(f"❌ Initial Score Mismatch: {initial.trinity_score}")

    # 2. Trigger Event: Manual Intervention (Friction)
    # Expected: Serenity decreases by 0.05
    print("\n[Action] Triggering MANUAL_INTERVENTION (-5.0 Filial Serenity)...")
    trinity_manager.apply_trigger("MANUAL_INTERVENTION")

    after_trigger = trinity_manager.get_current_metrics()
    print(f"[After Trigger] Serenity: {after_trigger.filial_serenity:.4f}")

    if after_trigger.filial_serenity == 0.95:
        print("✅ Delta Applied Correctly (1.0 -> 0.95)")
    else:
        print(f"❌ Delta Failed: {after_trigger.filial_serenity}")

    # 3. Trigger Event: Verification Success
    # Expected: Truth increases by 0.05 (Clamped at 1.0)
    print("\n[Action] Triggering VERIFICATION_SUCCESS (+5.0 Truth)...")
    trinity_manager.apply_trigger("VERIFICATION_SUCCESS")

    after_success = trinity_manager.get_current_metrics()
    print(f"[After Success] Truth: {after_success.truth:.4f}")

    if after_success.truth == 1.0:
        print("✅ Clamping Verified (Max 1.0 maintained)")
    else:
        print(f"❌ Clamping Failed: {after_success.truth}")

    # 4. Trigger Event: Verification Fail
    # Acc Deltas: Truth = +5 - 10 = -5 (-0.05). Goodness = +2 - 5 = -3 (-0.03).
    print("\n[Action] Triggering VERIFICATION_FAIL (-10.0 Truth, +5.0 Risk)...")
    trinity_manager.apply_trigger("VERIFICATION_FAIL")

    after_fail = trinity_manager.get_current_metrics()
    print(f"[After Fail] Truth: {after_fail.truth:.4f}, Goodness: {after_fail.goodness:.4f}")

    # Truth: 1.0 - 0.05 = 0.95. Goodness: 1.0 - 0.03 = 0.97
    if round(after_fail.truth, 2) == 0.95 and round(after_fail.goodness, 2) == 0.97:
        print("✅ Multi-Delta Verified (Accumulated State)")
    else:
        print(f"❌ Multi-Delta Failed: T={after_fail.truth}, G={after_fail.goodness}")


if __name__ == "__main__":
    verify_trinity_dynamic()
