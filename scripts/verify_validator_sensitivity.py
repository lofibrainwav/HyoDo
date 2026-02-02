import asyncio
import sys
from pathlib import Path

# Add package root to sys.path
sys.path.append(str(Path.cwd() / "packages" / "afo-core"))

from AFO.api.routes.integrity_check import IntegrityCheckRequest, check_integrity

TARGET_FILE = Path.cwd() / "packages/afo-core/AFO/api/routes/integrity_check.py"
SABOTAGE_CODE = '\n\n# SABOTAGE\n# Top-level assignment should always be checked\nx_fail: int = "this_should_fail_mypy"\n'


async def run_check(label: str):
    print(f"\n⚡ [{label}] Running Real-Time Integrity Check...")
    result = await check_integrity(IntegrityCheckRequest())
    truth_score = result["pillars"]["truth"]["score"]
    total_score = result["total_score"]
    print(f"   Truth Score: {truth_score}")
    print(f"   Total Score: {total_score}")
    return truth_score, total_score


async def stress_test():
    print("🥊 [Meta-Verification] Red Teaming Validator Protocol (Real-Time)")
    print("---------------------------------------------------")

    # 1. Baseline

    # 2. Sabotage: Inject Type Error into Source Code
    print(f"\n💉 SABOTAGE: Injecting Type Error into {TARGET_FILE.name}...")
    original_content = TARGET_FILE.read_text()

    try:
        # Append failing code
        TARGET_FILE.write_text(original_content + SABOTAGE_CODE)

        # 3. Verify Drop

        if t2 == 0:
            print("✅ SUCCESS: Score DROPPED to 0. Validator detected its own corruption.")
            print(f"   (Score dropped from {t1} -> {t2})")
        else:
            print(f"❌ FAILURE: Score is {t2}. MyPy did not catch the live injection!")

    finally:
        # 4. Restore
        print(f"\n❤️ RESTORE: Removing viral code from {TARGET_FILE.name}...")
        TARGET_FILE.write_text(original_content)

    # 5. Verify Recovery
    if t3 == 100:
        print("✅ SUCCESS: System recovered to 100.")
    else:
        print(f"❌ FAILURE: System did not recover (Score: {t3}).")

    print("\n---------------------------------------------------")
    if t1 == 100 and t2 == 0 and t3 == 100:
        print("🏆 META-VERIFICATION PASSED: The System possesses True Meta-Cognition.")
    else:
        print("💀 META-VERIFICATION FAILED.")


if __name__ == "__main__":
    asyncio.run(stress_test())
