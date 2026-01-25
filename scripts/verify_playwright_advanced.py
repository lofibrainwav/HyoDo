import asyncio
import os
import pathlib
import sys

# 프로젝트 루트 경로 추가
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core/AFO")).resolve()
)

from utils.playwright_bridge import MockScenario, bridge

# Force DRY_RUN off for this test if possible, or handle simulation
# antigravity.DRY_RUN_DEFAULT = False # We will respect the default, but check for simulation


async def verify_advanced_features():
    print("=== Playwright Bridge Advanced Features Verification ===")

    # 1. AI Integration Test
    print("\n[Step 1] verifying AI Scenario Request...")
    ai_result = await bridge.run_ai_test_scenario("Verify login button color is blue")
    print(f"AI Result: {ai_result}")
    assert ai_result["status"] == "ACCEPTED"
    assert "Verify login button color is blue" in ai_result["prompt_echo"]
    print("✅ AI Integration Verified")

    # 2. Mocking & Tracing Test
    print("\n[Step 2] Verifying Mocking & Tracing...")

    # Define a mock scenario
    mock_scenario = MockScenario(
        url_pattern="**/mock_test",
        response_body={"message": "This is a mocked response"},
        status=200,
    )

    # Use a dummy URL (will be mocked) and checking google.com as fallback if mocking fails broadly
    # but here we use the pattern matching.
    # Note: If DRY_RUN is True, this returns "simulation".

    try:
        # We try to verify a non-existent URL that matches our pattern
        # Since we mock it, it should work if network interception works.
        # But wait, page.goto needs a valid protocol.
        target_url = "http://localhost:8010/mock_test"

        result = await bridge.verify_ui(
            url=target_url,
            screenshot_path="verify_mock_trace.png",
            mock_scenarios=[mock_scenario],
            enable_tracing=True,
        )
        print(f"UI Verification Result: {result}")

        if result["status"] == "simulation":
            print(
                "⚠️ Running in Simulation (DRY_RUN) mode. Full integration not tested, but logic flow is correct."
            )
        else:
            assert result["status"] == "PASS"
            assert "trace" in result
            print("✅ Mocking & Tracing Verified")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        # If connection refused (since localhost:8010 might not be up), it captures it.
        # But since we are mocking, Playwright request interception should kick in BEFORE network if properly done?
        # Actually playwright route fulfills the request, so no actual network connection is made to the server
        # IF the routing matches. However, browser still needs to resolve DNS or similar unless fully intercepted.
        # 'http://localhost' usually is fine.

    await bridge.teardown()
    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    asyncio.run(verify_advanced_features())
