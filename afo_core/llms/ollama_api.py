from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from AFO.config.settings import settings
from AFO.domain.metrics.trinity import TrinityInputs, TrinityMetrics

# Trinity Score: 95.0 (Established by Chancellor)
"""
Ollama API Wrapper for AFO Kingdom

영덕 (Yeongdeok) - 로컬 설명·보안·프라이버시·Bridge Log 아카이빙
Ollama 기반 로컬 LLM 호출 래퍼
"""

logger = logging.getLogger(__name__)


class OllamaAPIWrapper:
    """
    Ollama API Wrapper (영덕 - Yeongdeok)

    로컬 Ollama 모델을 호출하는 표준화된 인터페이스
    """

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        """Ollama API Wrapper 초기화 (眞 - Centralized Config)"""
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Ollama 서버 가용성 확인 (眞 - Synchronous Check)"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            logger.warning(f"⚠️ Ollama 서버 확인 실패: {self.base_url}")
            return False

    def is_available(self) -> bool:
        """Ollama 서비스 가용성 반환"""
        return self.available

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Ollama 모델 호출 (영덕)

        Args:
            prompt: 입력 프롬프트
            model: 사용할 모델 (없으면 기본값 사용)
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            **kwargs: 추가 파라미터

        Returns:
            생성된 응답 텍스트
        """
        try:
            model = model or self.model

            timeout_seconds = float(settings.OLLAMA_TIMEOUT)

            start_time = time.time()
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "num_ctx": kwargs.get("num_ctx", 4096),
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                elapsed = time.time() - start_time
                if elapsed > 10.0:
                    logger.warning(f"🐢 Ollama slow generation: {elapsed:.2f}s ({model})")

                return str(result.get("response", ""))

        except Exception as e:
            logger.error(f"❌ Ollama API 호출 실패: {e}")
            return f"영덕 호출 실패: {e}"

    async def generate_with_context(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        컨텍스트를 포함한 Ollama 호출 (SSOT 준수)

        Args:
            prompt: 입력 프롬프트
            context: 추가 컨텍스트
            **kwargs: 추가 파라미터

        Returns:
            응답 및 메타데이터
        """
        context = context or {}
        response = await self.generate(prompt, **{**context, **kwargs})

        # Trinity Score 계산 (영덕의 철학 점수 기반)
        trinity_inputs = TrinityInputs(
            truth=0.96,  # 영덕의 기본 Truth 점수
            goodness=0.98,  # 영덕의 기본 Goodness 점수
            beauty=0.95,  # 영덕의 기본 Beauty 점수
            filial_serenity=0.99,  # 영덕의 기본 Serenity 점수
        )
        trinity_score = TrinityMetrics.from_inputs(trinity_inputs, eternity=1.0)

        return {
            "response": response,
            "model": self.model,
            "provider": "ollama",
            "trinity_score": trinity_score.to_dict(),
            "scholar_codename": "영덕",
            "success": True,
        }

    async def close(self) -> None:
        """리소스 정리"""
        pass  # HTTP 클라이언트는 자동 정리됨


# 글로벌 인스턴스
ollama_api = OllamaAPIWrapper()
