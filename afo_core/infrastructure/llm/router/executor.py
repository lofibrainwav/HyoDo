from __future__ import annotations

import logging
from typing import Any

from AFO.api_wallet import APIWallet
from AFO.config.settings import settings
from AFO.llms.claude_api import ClaudeAPIWrapper
from AFO.llms.codex_api import CodexAPIWrapper
from AFO.llms.gemini_api import GeminiAPIWrapper
from AFO.llms.ollama_api import OllamaAPIWrapper

logger = logging.getLogger(__name__)


class ScholarExecutor:
    """Execution Logic for calling various scholars/LLM providers"""

    def __init__(self) -> None:
        self._initialize_api_wallet()

    def _initialize_api_wallet(self) -> None:
        """API Wallet 초기화"""
        try:
            self.api_wallet = APIWallet()
            logger.info("✅ API Wallet initialized for SSOT compliance")
        except ImportError as e:
            logger.error(f"❌ API Wallet import failed: {e}")
            self.api_wallet = None
        except Exception as e:
            logger.error(f"❌ API Wallet initialization failed: {e}")
            self.api_wallet = None

    async def execute_scholar_call(
        self,
        scholar_key: str,
        wallet_config: dict[str, Any],
        query: str,
        context: dict[str, Any],
        scholars_config: dict[str, Any],
    ) -> dict[str, Any]:
        """학자별 실제 호출 실행 분기"""
        # Pillar 학자들은 Ollama로 라우팅 (로컬 LLM 기반 평가)
        pillar_scholars = {
            "truth_scholar",
            "goodness_scholar",
            "beauty_scholar",
            "serenity_scholar",
            "eternity_scholar",
        }

        if scholar_key == "ollama" or scholar_key in pillar_scholars:
            # Pillar 학자는 scholar_config에서 provider 확인
            scholar_config = scholars_config.get(scholar_key, {})
            if scholar_config.get("provider") == "ollama" or scholar_key == "ollama":
                return await self._call_ollama_via_wallet(wallet_config, query, context)

        if scholar_key == "claude":
            return await self._call_claude_via_wallet(wallet_config, query, context)
        elif scholar_key == "gemini":
            return await self._call_gemini_via_wallet(wallet_config, query, context)
        elif scholar_key == "codex":
            return await self._call_codex_via_wallet(wallet_config, query, context)
        else:
            # Unknown scholar - 기본적으로 Ollama로 폴백
            logger.warning(f"⚠️ Unknown scholar '{scholar_key}', falling back to Ollama")
            return await self._call_ollama_via_wallet(wallet_config, query, context)

    async def _call_ollama_via_wallet(
        self, wallet_config: dict[str, Any], query: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Ollama 학자 호출 (영덕)"""
        try:
            model = wallet_config.get("model", settings.OLLAMA_MODEL)
            base_url = wallet_config.get("base_url", settings.OLLAMA_BASE_URL)

            ollama = OllamaAPIWrapper(base_url=base_url, model=model)
            response = await ollama.generate(query, **context)

            return {
                "success": True,
                "response": response,
                "model": model,
                "provider": "ollama",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"영덕 호출 실패: {e}",
                "provider": "ollama",
            }

    async def _call_claude_via_wallet(
        self, wallet_config: dict[str, Any], query: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Claude 학자 호출 (자룡)"""
        try:
            api_key = wallet_config.get("api_key")
            if not api_key:
                raise ValueError("Claude API key not found in wallet")

            claude = ClaudeAPIWrapper(api_key=api_key)
            response = await claude.generate(query, **context)

            return {
                "success": True,
                "response": response,
                "model": "claude-3.5-sonnet",
                "provider": "anthropic",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"자룡 호출 실패: {e}",
                "provider": "anthropic",
            }

    async def _call_gemini_via_wallet(
        self, wallet_config: dict[str, Any], query: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Gemini 학자 호출 (육손)"""
        try:
            api_key = wallet_config.get("api_key")
            if not api_key:
                raise ValueError("Gemini API key not found in wallet")

            gemini = GeminiAPIWrapper(api_key=api_key)
            response = await gemini.generate(query, **context)

            return {
                "success": True,
                "response": response,
                "model": "gemini-2.0-flash",
                "provider": "google",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"육손 호출 실패: {e}",
                "provider": "google",
            }

    async def _call_codex_via_wallet(
        self, wallet_config: dict[str, Any], query: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Codex 학자 호출 (방통)"""
        try:
            api_key = wallet_config.get("api_key")
            if not api_key:
                raise ValueError("Codex API key not found in wallet")

            codex = CodexAPIWrapper(api_key=api_key)
            response = await codex.generate(query, **context)

            return {
                "success": True,
                "response": response,
                "model": "codex",
                "provider": "openai",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"방통 호출 실패: {e}",
                "provider": "openai",
            }
