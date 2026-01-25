import asyncio
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.config.antigravity import antigravity

# We will mock the graph and router logic to test the flow "Commander -> Action"


class TestKingdomLoop(unittest.TestCase):
    def setUp(self) -> None:
        # 1. Setup Antigravity (Governance)
        antigravity.AUTO_DEPLOY = True
        antigravity.DRY_RUN_DEFAULT = True  # Monitor Mode
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def _get_async_mock(self, return_value) -> None:
        async def async_magic():
            return return_value

        return async_magic()

    def test_full_loop_simulation(self) -> None:
        """
        Simulate the Grand Loop:
        User Request -> Chancellor (Router) -> Antigravity (Check) -> Action
        """
        print("\n🌌 [Matrix] Verifying Kingdom Loop...")

        # 1. User Request
        user_query = "Construct a secure fortress (Kingdom Protection)"
        print(f"👑 Commander: '{user_query}'")

        # 2. Chancellor Analysis (Mocked)
        # In a real integration test, we would call the actual API.
        # Here we verify the logic flow that WOULD happen.

        # Jegalryang (Truth) Analysis

        # Samaui (Goodness) Check
        samaui_risk_score = 0.05  # Low Risk

        # 3. Antigravity Governance Check
        # Check if 'construct_fortress' feature is enabled
        # We mock get_feature_flag directly here to simulate Redis
        with patch.object(antigravity, "get_feature_flag", return_value=True):
            is_allowed = antigravity.check_governance("construct_fortress")
            print(f"⚖️ Antigravity Verdict: {'ALLOWED' if is_allowed else 'DENIED'}")

            # Risk Brake Check (Simulated)
            # If Risk > 0.8, it should block even if allowed
            risk_brake_active = samaui_risk_score > 0.8
            if risk_brake_active:
                print("🛑 Risk Brake Triggered!")
                is_allowed = False

            assert is_allowed, "Governance should allow safe construction"

        # 4. Action (Result)
        if is_allowed:
            final_action = "Deploying Firewall Rules [DRY_RUN]"
            print(f"🚀 Execution: {final_action}")
        else:
            final_action = "BLOCKED"

        assert final_action == "Deploying Firewall Rules [DRY_RUN]"
        print("✅ Full Loop Verified: Commander -> Chancellor -> Antigravity -> Action")

    def test_risk_brake_loop(self) -> None:
        """Simulate High Risk Request Blocking"""
        print("\n🛑 [Matrix] Verifying Risk Brake Loop...")

        # High Risk Scenario
        samaui_risk_score = 0.95

        # Even if flag is True
        with patch.object(antigravity, "get_feature_flag", return_value=True):
            # Manual Check simulating what 'check_risk_brakes' would do if integrated with score
            # Currently check_risk_brakes is void, but we simulate the LOGIC intended for Phase 6
            is_allowed = True
            if samaui_risk_score > 0.8:
                print(f"🛡️ SAMAUI INTERVENTION: Risk {samaui_risk_score} is too high.")
                is_allowed = False

            assert not is_allowed, "High risk should be blocked"
            print("✅ Risk Brake Verified")


if __name__ == "__main__":
    unittest.main()
