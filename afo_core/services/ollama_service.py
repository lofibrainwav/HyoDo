# Trinity Score: 95.0 (眞善美 준수)
"""
AFO Ollama Service - Robust Switching Protocol
TICKET-094-P Implementation: Health -> Warm-up -> Atomic Swap
"""

import asyncio
import logging
import os
import time
from typing import Any

import httpx

from AFO.config.settings import get_settings

logger = logging.getLogger("AFO.OllamaService")


class OllamaService:
    """
    Ollama Service with a 3-step switching protocol:
    1. Health Check: Target model check via /api/tags
    2. Warm-up: Ping target model via /api/generate
    3. Atomic Swap: Update internal reference
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._active_model: str = self.settings.OLLAMA_MODEL
        self._switch_lock = asyncio.Lock()
        self._last_switch_ts: float = 0
        self._metrics = {"switch_count": 0, "failed_switches": 0, "last_error": None}

    @property
    def active_model(self) -> str:
        return self._active_model

    async def ensure_model(self, target_model: str) -> bool:
        """
        Ensures target_model is active using the 3-step protocol.
        """
        if self._active_model == target_model:
            return True

        async with self._switch_lock:
            # Re-check after acquiring lock (double-checked locking pattern)
            if self._active_model == target_model:
                return True

            logger.info(f"🔄 [Step 0] Switching started: {self._active_model} -> {target_model}")

            try:
                # 1. Health Check
                if not await self._check_health(target_model):
                    raise RuntimeError(f"Model {target_model} not found in Ollama tags")
                logger.debug(f"✅ [Step 1] Health Check OK: {target_model}")

                # 2. Warm-up
                if not await self._warm_up(target_model):
                    raise RuntimeError(f"Warm-up failed for model {target_model}")
                logger.debug(f"✅ [Step 2] Warm-up complete: {target_model}")

                # 3. Atomic Swap
                old_model = self._active_model
                self._active_model = target_model
                self._last_switch_ts = time.time()
                self._metrics["switch_count"] += 1

                logger.info(f"✅ [Step 3] Atomic Swap Success: {old_model} -> {target_model}")
                return True

            except Exception as e:
                self._metrics["failed_switches"] += 1
                self._metrics["last_error"] = str(e)
                logger.error(f"❌ Ollama Switch Failed: {e}")
                return False

    async def _check_health(self, model: str) -> bool:
        """Step 1: Verify model presence."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.settings.OLLAMA_BASE_URL}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                # Check for exact match or with :latest tag
                return model in models or f"{model}:latest" in models
        except Exception as e:
            logger.warning(f"Health check error: {e}")
            return False

    async def _warm_up(self, model: str) -> bool:
        """Step 2: Trigger model load without heavy inference."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model,
                    "prompt": "ping",
                    "stream": False,
                    "options": {"num_predict": 1},
                }
                response = await client.post(
                    f"{self.settings.OLLAMA_BASE_URL}/api/generate", json=payload
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Warm-up error: {e}")
            return False

    def get_status(self) -> dict[str, Any]:
        """Return service status for Dashboard/SSOT."""
        return {
            "active_model": self._active_model,
            "last_switch": self._last_switch_ts,
            "metrics": self._metrics,
            "head_sha": os.getenv("GIT_COMMIT_SHA", "unknown"),
        }


# Singleton
ollama_service = OllamaService()
