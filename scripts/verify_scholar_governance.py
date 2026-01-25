import asyncio
import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch

# Path setup is critical for imports from packages
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.config import antigravity
from AFO.scholars.jaryong import JaryongScholar


class TestScholarGovernance(unittest.TestCase):
    def setUp(self) -> None:
        # 1. Mock API wrapper
        self.mock_api = MagicMock()
        # 2. Setup Async Helper
        # We don't set a return value yet; tests will set it using _get_async_mock

        # 3. Initialize Jaryong with mocked API
        self.jaryong = JaryongScholar(api_wrapper=self.mock_api)

    def _get_async_mock(self, return_value) -> None:
        """Helper to create an awaitable mock result"""

        async def async_magic():
            return return_value

        return async_magic()

    @patch.object(antigravity, "check_governance")
    def test_scholar_blocked_flag(self, mock_flag) -> None:
        """Test blocking when flag is False"""
        print("\n🧪 Testing Scholar Blocked by Flag...")
        mock_flag.return_value = False

        # Action
        result = asyncio.run(self.jaryong.verify_logic("print('hello')"))

        # Assert
        assert "Governance Denied" in result
        print("✅ Correctly BLOCKED by Flag.")

    @patch.object(antigravity, "check_governance")
    def test_scholar_allowed_flag(self, mock_flag) -> None:
        """Test allowing when flag is True"""
        print("\n🧪 Testing Scholar Allowed by Flag...")
        mock_flag.return_value = True

        # Mock successful API response
        self.mock_api.generate_with_context.return_value = self._get_async_mock(
            {
                "success": True,
                "content": "Analysis Complete",
            }
        )

        # Action
        result = asyncio.run(self.jaryong.verify_logic("print('hello')"))

        # Assert
        assert "Governance Denied" not in result
        assert "Analysis Complete" in result
        print("✅ Correctly ALLOWED by Flag.")

    @patch.object(antigravity, "check_governance")
    def test_scholar_risk_brake(self, mock_flag) -> None:
        """Test Risk Brake on dangerous code"""
        print("\n🧪 Testing Scholar Blocked by Risk Brake (eval)...")
        mock_flag.return_value = True

        # 'eval(' triggers local risk brake in jaryong.py
        dangerous_code = 'eval(\'__import__("subprocess").run(["echo","blocked"], check=False)\')'

        # Action
        result = asyncio.run(self.jaryong.verify_logic(dangerous_code))

        # Assert
        assert "Governance Denied" in result
        # Verify Governance Check directly
        assert not self.jaryong._check_governance("jaryong", dangerous_code)
        print("✅ Correctly BLOCKED by Risk Brake.")


if __name__ == "__main__":
    unittest.main()
