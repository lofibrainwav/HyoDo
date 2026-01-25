from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from httpx import AsyncClient

from AFO.config.settings import settings
from AFO.security.vault_manager import vault as v1

# Trinity Score: 92.0 (Established by Chancellor - Hardened)
"""
OpenAI API Wrapper
하이브리드 LLM 전략을 위한 OpenAI REST API 연동
"""


logger = logging.getLogger(__name__)


class OpenAIAPIWrapper:
    """
    OpenAI API 직접 연동
    월 구독제 CLI 대신 REST API 사용
    """

    def __init__(self) -> None:
        # Phase 35-1: Centralized Config Integration (眞 - Truth)
        self.api_key: str | None = settings.OPENAI_API_KEY

        # Fallback to Vault if not in settings/env
        if not self.api_key:
            try:
                self.api_key = v1.get_secret("OPENAI_API_KEY")
            except Exception:
                pass

        self.chatgpt_token: str | None = (
            settings.CHATGPT_SESSION_TOKEN_1
            or settings.CHATGPT_SESSION_TOKEN_2
            or settings.CHATGPT_SESSION_TOKEN_3
        )
        self.base_url = "https://api.openai.com"
        self.chatgpt_web_url = "https://chat.openai.com/api"

        # API 키 우선 사용
        self.available: bool = bool(self.api_key)
        self.client: httpx.Optional[AsyncClient] = None
        self.use_chatgpt_web = False

        if self.api_key:
            # 직접 OpenAI API 사용
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            logger.info("✅ OpenAI API Wrapper 초기화 완료 (OpenAI API 키 사용)")
        elif self.chatgpt_token:
            # ChatGPT 세션 토큰 발견 (웹 인터페이스용)
            # 주의: 세션 토큰으로는 OpenAI API를 직접 호출할 수 없음
            logger.warning("⚠️ CHATGPT_SESSION_TOKEN 발견되었으나 OpenAI API 호출 불가")
            logger.info(
                "💡 ChatGPT 세션 토큰은 웹 인터페이스용이며, API 호출에는 OPENAI_API_KEY가 필요합니다"
            )
            logger.info(
                "   또는 API Wallet에 'openai' 키를 등록하세요: python3 AFO/api_wallet.py add openai <YOUR_KEY>"
            )
            self.available = False
        else:
            # CLI 정기구독 사용 시 API 키 불필요 - 경고 대신 debug
            logger.debug("OPENAI_API_KEY 없음 - OpenAI API 비활성화 (CLI 사용 시 무시)")

    async def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """
        OpenAI API로 텍스트 생성
        """
        if not self.available or not self.client:
            return {
                "error": "OpenAI API not available",
                "fallback": f"[OpenAI Unavailable] {prompt[:50]}...",
            }

        try:
            request_data = {
                "model": kwargs.get("model", "gpt-4o"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 1024),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }

            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions", json=request_data
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])

                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    finish_reason = choices[0].get("finish_reason")

                    return {
                        "success": True,
                        "content": content,
                        "model": result.get("model", "gpt-4o"),
                        "finish_reason": finish_reason,
                        "usage": result.get("usage", {}),
                    }
                else:
                    return {
                        "error": "No choices in OpenAI response",
                        "full_response": result,
                    }
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                except Exception:
                    error_msg = response.text or "Unknown error"

                return {
                    "error": f"OpenAI API error: {error_msg}",
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"OpenAI API exception: {e}")
            return {"error": f"OpenAI API exception: {e!s}"}

    async def embed(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        """
        OpenAI API로 텍스트 임베딩 생성 (TICKET-054 Renaissance)
        """
        if not self.available or not self.client:
            logger.error("OpenAI API not available for embedding")
            return []

        try:
            request_data = {
                "model": model,
                "input": text,
            }

            response = await self.client.post(f"{self.base_url}/v1/embeddings", json=request_data)

            if response.status_code == 200:
                result = response.json()
                data = result.get("data", [])
                if data:
                    return data[0].get("embedding", [])
                return []
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"OpenAI Embedding error: {error_msg}")
                return []
        except Exception as e:
            logger.error(f"OpenAI Embedding exception: {e}")
            return []

    async def generate_with_context(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """
        대화 맥락을 포함한 생성
        """
        if not self.available or not self.client:
            return {
                "error": "OpenAI API not available",
                "fallback": "[OpenAI Unavailable] Context-based response",
            }

        try:
            # 메시지 포맷 검증 및 변환
            formatted_messages = []
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role in ["system", "user", "assistant"]:
                    formatted_messages.append({"role": role, "content": content})

            request_data = {
                "model": kwargs.get("model", "gpt-4o"),
                "messages": formatted_messages,
                "max_tokens": kwargs.get("max_tokens", 2048),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }

            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions", json=request_data
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])

                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    finish_reason = choices[0].get("finish_reason")

                    return {
                        "success": True,
                        "content": content,
                        "model": result.get("model", "gpt-4o"),
                        "finish_reason": finish_reason,
                        "usage": result.get("usage", {}),
                    }
                else:
                    return {"error": "No choices in OpenAI response"}
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                return {
                    "error": f"OpenAI API error: {error_msg}",
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"OpenAI API context exception: {e}")
            return {"error": f"OpenAI API exception: {e!s}"}

    async def close(self) -> None:
        """리소스 정리"""
        if self.client:
            await self.client.aclose()

    def is_available(self) -> bool:
        """API 사용 가능 여부"""
        return self.available

    def get_models(self) -> list[str]:
        """사용 가능한 모델 목록"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]

    def get_cost_estimate(self, tokens: int) -> float:
        """비용 추정 (달러)"""
        # GPT-4o 비용 (2024년 기준)
        # GPT-4o: $5/M input tokens, $15/M output tokens
        input_cost_per_million = 5.0
        output_cost_per_million = 15.0

        # 대략적인 추정: 입력 토큰의 20%가 출력 토큰
        input_tokens = tokens * 0.8
        output_tokens = tokens * 0.2

        cost = (input_tokens / 1_000_000) * input_cost_per_million + (
            output_tokens / 1_000_000
        ) * output_cost_per_million

        return cost


# 글로벌 인스턴스
openai_api = OpenAIAPIWrapper()


if __name__ == "__main__":
    # 테스트
    async def test_openai_api() -> None:
        print("🤖 OpenAI API Wrapper 테스트")
        print("=" * 50)

        if not openai_api.is_available():
            print("❌ OpenAI API 키가 설정되지 않음")
            print("   환경변수 OPENAI_API_KEY를 설정해주세요")
            return

        test_prompt = "안녕하세요! 당신은 누구인가요?"

        print(f"🔍 테스트 프롬프트: {test_prompt}")

        try:
            result = await openai_api.generate(test_prompt, max_tokens=200)

            if result.get("success"):
                print("✅ 성공!")
                print(f"📝 응답: {result['content'][:100]}...")
                print(f"🤖 모델: {result['model']}")
                if "usage" in result:
                    print(f"📊 사용량: {result['usage']}")
            else:
                print(f"❌ 실패: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ 예외: {e}")

        await openai_api.close()

    asyncio.run(test_openai_api())
