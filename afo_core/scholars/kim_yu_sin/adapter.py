from __future__ import annotations

import logging
import platform
import time

import httpx

from AFO.config.settings import get_settings

logger = logging.getLogger(__name__)

# MLX Import (Conditional)
try:
    import mlx.core as mx  # type: ignore[import]

    MLX_AVAILABLE = True
except ImportError:
    mx = None  # type: ignore[assignment]
    MLX_AVAILABLE = False


class OllamaAdapter:
    """Ollama 및 MLX 통신 어댑터"""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.OLLAMA_BASE_URL
        self._mlx_available = self._check_mlx_availability()

    @property
    def is_mlx_available(self) -> bool:
        return self._mlx_available

    def _check_mlx_availability(self) -> bool:
        """
        Enhanced MLX availability check for Phase 2-3 optimization.
        Returns True if MLX is available (Apple Silicon), False otherwise (Docker/Linux).
        Prevents repetitive try/except overhead on every call.
        """
        system = platform.system().lower()

        # Quick platform check: MLX only works on macOS with Apple Silicon
        if system != "darwin":
            logger.info("ℹ️ [Yeongdeok] Non-macOS environment detected. Skipping MLX check.")
            return False

        try:
            # Simple functional check with timeout
            if mx is None:
                logger.info("ℹ️ [Yeongdeok] MLX is None, skipping functional check.")
                return False

            start_time = time.time()
            _ = mx.array([1])  # type: ignore[attr-defined]
            check_time = time.time() - start_time

            if check_time > 1.0:  # Slow initialization might indicate issues
                logger.warning(
                    f"⚠️ [Yeongdeok] MLX initialization slow ({check_time:.2f}s). May impact performance."
                )
                return True  # Still available but warn

            logger.info("✅ [Yeongdeok] MLX Acceleration Available (Apple Silicon Native)")
            return True

        except ImportError:
            logger.info("ℹ️ [Yeongdeok] MLX Not Found (Running in Docker/Linux Standard Mode)")
            return False
        except Exception as e:
            logger.warning(f"⚠️ [Yeongdeok] MLX Check Failed: {e}. Disabling MLX Optimization.")
            return False

    async def call_ollama(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
        model: str | None = None,
        default_model: str = "qwen2.5-coder:7b",
    ) -> str:
        """Ollama API 호출 (Model override 가능)"""
        target_model = model or default_model
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                payload = {
                    "model": target_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_ctx": 4096},
                }
                if system:
                    payload["system"] = system

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()
                    return str(result.get("response", ""))
                else:
                    logger.error(f"Ollama Error ({target_model}): {response.text}")
                    return f"Ollama 호출 실패 ({response.status_code})"

        except Exception as e:
            logger.error(f"Yeongdeok ({target_model}) failed: {e}")
            return f"처리 실패: {e!s}"
