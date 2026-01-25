import os
import pathlib
import sys
import unittest
from unittest.mock import patch

# Path setup to ensure imports work
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.config.antigravity import antigravity
from AFO.genui.genui_orchestrator import GenUIOrchestrator


class TestGenUIEvolution(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = GenUIOrchestrator()

    @patch.object(antigravity, "get_feature_flag")
    def test_rollout_zero_percent(self, mock_flag) -> None:
        """Test blocking when flag is False (0% rollout or disabled)"""
        print("\n🧪 Testing 0% Rollout / Disabled Flag...")
        mock_flag.return_value = False

        result = self.orchestrator.create_project("test_blocked", "dashboard")

        assert result.get("status") == "BLOCKED_BY_GOVERNANCE"
        print("✅ Correctly BLOCKED by Governance.")

    @patch.object(antigravity, "get_feature_flag")
    @patch("AFO.genui.genui_orchestrator.PlaywrightBridgeMCP")
    def test_rollout_hundred_percent(self, mock_playwright, mock_flag) -> None:
        """Test allowing when flag is True (100% rollout)"""
        print("\n🧪 Testing 100% Rollout / Enabled Flag...")
        mock_flag.return_value = True

        # Mock Playwright to avoid real browser calls
        mock_playwright.navigate.return_value = {"success": True}
        mock_playwright.screenshot.return_value = {"success": True}

        result = self.orchestrator.create_project("test_allowed", "dashboard")

        assert result.get("status") != "BLOCKED_BY_GOVERNANCE"
        assert "code_path" in result
        print("✅ Correctly ALLOWED by Governance.")

    @patch.object(antigravity, "get_feature_flag")
    def test_vision_blocked(self, mock_flag) -> None:
        """Test allowing creation but blocking vision"""
        print("\n🧪 Testing Vision Blocked...")

        # check_governance is called twice:
        # 1. genui_create -> True (Allow creation)
        # 2. genui_vision -> False (Block vision)
        mock_flag.side_effect = [True, False]

        result = self.orchestrator.create_project("test_vision_block", "dashboard")

        assert result.get("status") != "BLOCKED_BY_GOVERNANCE"

        # Verify vision result failure message or state
        vision = result.get("vision_result", {})
        assert not vision.get("success")
        print("✅ Correctly BLOCKED Vision while allowing Creation.")


if __name__ == "__main__":
    unittest.main()
