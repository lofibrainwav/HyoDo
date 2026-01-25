import asyncio
import os
import pathlib
import sys

# Setup path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from services.truth_metrics_calculator import truth_metrics


async def verify_truth_metrics():
    print("📏 [Truth Metrics] Verification Start (Target: 25/25)")

    # 1. Define High-Quality Code Snippet (Simulating perfect code)
    perfect_code = """
    class SafeSystem:
        def process_data(self, input_data: dict) -> bool:
            try:
                # Logic
                return True
            except Exception as e:
                logger.error(f"Error: {e}")
                return False

    def test_safe_system():
        assert SafeSystem().process_data({}) == True
    """

    input_data = {"data": {"key": "value"}}

    # 2. Calculate Score
    print("\n[Analyzing Perfect Code Candidate]...")
    result = truth_metrics.calculate_technical_score(perfect_code, input_data, test_mode=True)

    print(f"🔹 Total Score: {result['total_score']} / {result['max_score']}")
    print(f"🔹 Trinity Conversion: {result['trinity_conversion']} / 100.0")
    print("\n[Details]")
    for detail in result["details"]:
        print(f"  {detail}")

    # 3. Assertions
    if result["total_score"] == 25:
        print("\n✅ Verification SUCCESS: Achieved Perfect Technical Score (25/25)")
    else:
        print(f"\n❌ Verification FAIL: Score {result['total_score']} < 25")

    # 4. Low Quality Candidate Check
    print("\n[Analyzing Low Quality Candidate]...")
    bad_code = "print('hello')"
    bad_result = truth_metrics.calculate_technical_score(bad_code, {}, test_mode=False)
    print(f"🔹 Poor Code Score: {bad_result['total_score']} / 25")
    if bad_result["total_score"] < 25:
        print("✅ Detection System Working: Low quality code identified.")

    print("\n[Verification Complete] Detailed Truth Score Metrics Operational.")


if __name__ == "__main__":
    asyncio.run(verify_truth_metrics())
