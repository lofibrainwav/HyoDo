# Trinity Score: 90.0 (Established by Chancellor)
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip Yeongdeok tests in CI (Ollama not available)
SKIP_OLLAMA_TESTS = os.getenv("CI", "").lower() in ("true", "1") or not os.getenv("OLLAMA_HOST")

# Add root directory to sys.path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from AFO.scholars.bangtong import BangtongScholar
from AFO.scholars.jaryong import JaryongScholar
from AFO.scholars.kim_yu_sin import KimYuSinScholar
from AFO.scholars.yukson import YuksonScholar


# Helper for consistent mock responses
def mock_api_response(content="Mock Content", success=True, error=None) -> None:
    return {"content": content, "success": success, "error": error}


class TestScholarsBehavior(unittest.IsolatedAsyncioTestCase):
    # --- Bangtong (Codex) Tests ---

    async def test_bangtong_implement_success(self):
        """Bangtong implement success scenario"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response("def foo(): pass")

        scholar = BangtongScholar(api_wrapper=mock_api)
        result = await scholar.implement("Create a function")

        self.assertEqual(result, "def foo(): pass")
        call_args = mock_api.generate_with_context.call_args
        self.assertIn("codex-cli", call_args.kwargs["model"])

    async def test_bangtong_implement_failure(self):
        """Bangtong implement failure scenario"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response(
            success=False, error="API Error"
        )

        scholar = BangtongScholar(api_wrapper=mock_api)
        result = await scholar.implement("Fail please")

        self.assertIn("구현 실패", result)

    async def test_bangtong_review(self):
        """Bangtong review implementation"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response("Code looks good")

        scholar = BangtongScholar(api_wrapper=mock_api)
        result = await scholar.review_implementation("print('hi')")

        self.assertEqual(result, "Code looks good")

    # --- Jaryong (Claude) Tests ---

    @patch("AFO.scholars.jaryong.JaryongScholar._check_governance", return_value=True)
    async def test_jaryong_verify_logic(self, mock_gov):
        """Jaryong verify logic success"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response("Logic Verified")

        scholar = JaryongScholar(api_wrapper=mock_api)
        result = await scholar.verify_logic("print('hello')")

        self.assertEqual(result, "Logic Verified")
        call_args = mock_api.generate_with_context.call_args
        self.assertIn("claude-code-cli", call_args.kwargs["model"])

    @patch("AFO.scholars.jaryong.JaryongScholar._check_governance", return_value=True)
    async def test_jaryong_refactor(self, mock_gov):
        """Jaryong suggest refactoring"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response("Refactored Code")

        scholar = JaryongScholar(api_wrapper=mock_api)
        result = await scholar.suggest_refactoring("messy code")

        self.assertEqual(result, "Refactored Code")

    # --- Yukson (Gemini) Tests ---

    async def test_yukson_strategy(self):
        """Yukson advise strategy"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response("Strategic Plan")

        scholar = YuksonScholar(api_wrapper=mock_api)
        result = await scholar.advise_strategy("Win Battle")

        self.assertEqual(result, "Strategic Plan")
        call_args = mock_api.generate_with_context.call_args
        self.assertIn("gemini-1.5-pro", call_args.kwargs["model"])

    async def test_yukson_strategy_failure(self):
        """Yukson advise strategy failure"""
        mock_api = AsyncMock()
        mock_api.generate_with_context.return_value = mock_api_response(
            success=False, error="Strategy Error"
        )

        scholar = YuksonScholar(api_wrapper=mock_api)
        result = await scholar.advise_strategy("Fail")

        self.assertIn("전략 수립 실패", result)

    # --- Yeongdeok (Ollama) Tests ---

    @pytest.mark.skipif(SKIP_OLLAMA_TESTS, reason="Ollama not available in CI")
    @patch(
        "AFO.scholars.kim_yu_sin.adapter.OllamaAdapter._check_mlx_availability",
        return_value=False,
    )
    @patch("AFO.scholars.kim_yu_sin.httpx.AsyncClient")
    async def test_kim_yu_sin_document_code(self, mock_client_cls, mock_mlx_check):
        """Yeongdeok document code using mocked HTTP client (Force fallback by disabling MLX)"""
        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client_instance

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Documentation Content"}
        mock_client_instance.post.return_value = mock_response

        # Re-instantiate to trigger mocked check
        scholar = KimYuSinScholar()
        scholar.adapter.base_url = "http://test-ollama:11434"

        result = await scholar.document_code("def foo():")

        self.assertEqual(result, "Documentation Content")
        # Verify call
        call_args = mock_client_instance.post.call_args
        self.assertEqual(call_args.args[0], "http://test-ollama:11434/api/generate")
        self.assertIn("def foo():", call_args.kwargs["json"]["prompt"])

    @pytest.mark.skipif(SKIP_OLLAMA_TESTS, reason="Ollama not available in CI")
    @patch("AFO.scholars.kim_yu_sin.httpx.AsyncClient")
    async def test_kim_yu_sin_http_failure(self, mock_client_cls):
        """Yeongdeok HTTP 500 failure"""
        mock_client_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Error"
        mock_client_instance.post.return_value = mock_response

        # Re-instantiate to avoid shared state issues in parallel runs
        scholar = KimYuSinScholar()
        scholar.adapter.base_url = "http://test-ollama-fail:11434"

        try:
            result = await scholar.summarize_log("log data")
            self.assertIn("Ollama 호출 실패", result)
        finally:
            # Explicitly cleanup if needed, though AsyncMock usually handles it
            pass

    @pytest.mark.skipif(SKIP_OLLAMA_TESTS, reason="Ollama not available in CI")
    @patch("AFO.scholars.kim_yu_sin.httpx.AsyncClient")
    async def test_kim_yu_sin_security_scan(self, mock_client_cls):
        """Yeongdeok security scan"""
        mock_client_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "No secrets found"}
        mock_client_instance.post.return_value = mock_response

        scholar = KimYuSinScholar()
        result = await scholar.security_scan("password = 123")

        self.assertEqual(result, "No secrets found")


if __name__ == "__main__":
    unittest.main()
