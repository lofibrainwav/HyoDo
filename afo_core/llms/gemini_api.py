from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

import httpx

from AFO.api_wallet import create_wallet
from AFO.config.settings import settings

# Trinity Score: 90.0 (Established by Chancellor)
"""
Gemini API Wrapper
하이브리드 LLM 전략을 위한 Google Gemini REST API 연동

CLI 없이 직접 API 호출로 월 구독제 LLM 통합
"""

logger = logging.getLogger(__name__)


class GeminiAPIWrapper:
    """
    Google Gemini API 직접 연동
    월 구독제 CLI 대신 REST API 사용
    """

    def __init__(self) -> None:
        """Gemini API Wrapper 초기화 (眞 - Centralized Config)"""
        # 1순위: settings.GEMINI_API_KEY
        # 2순위: API Wallet (암호화 저장소)
        self.api_key = settings.GEMINI_API_KEY

        # API Wallet 연동 (폴백)
        if not self.api_key:
            try:
                wallet = create_wallet()
                self.api_key = wallet.get("gemini", decrypt=True) or wallet.get(
                    "google", decrypt=True
                )
                if self.api_key:
                    logger.info("✅ API Wallet에서 Gemini/Google 키 로드 성공")
            except Exception as e:
                logger.debug(f"API Wallet 연동 실패 (무시됨): {e}")

        self.base_url = "https://generativelanguage.googleapis.com"
        self.available: bool = bool(self.api_key)
        self.client: httpx.AsyncClient | None = None

        if self.available:
            self.client = httpx.AsyncClient(timeout=30.0)
            logger.info("✅ Gemini API Wrapper 초기화 완료")
        else:
            # 서버 시작 시점에서는 조용히 처리 (optional dependency)

            if hasattr(sys, "_getframe") and "api_server" in str(
                sys._getframe(0).f_code.co_filename
            ):
                # 서버 시작 시에는 로깅하지 않음
                pass
            else:
                # CLI 정기구독 사용 시 API 키 불필요
                logger.debug("GEMINI_API_KEY 없음 - Gemini API 비활성화 (CLI 사용 시 무시)")

    async def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """
        Gemini API로 텍스트 생성
        """
        if not self.available or not self.client:
            return {
                "error": "Gemini API not available",
                "fallback": f"[Gemini Unavailable] {prompt[:50]}...",
            }

        try:
            model = kwargs.get("model", "gemini-1.5-pro")
            url = f"{self.base_url}/v1beta/models/{model}:generateContent"

            request_data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 1024),
                    "topP": 0.95,
                    "topK": 40,
                },
            }

            params = {"key": self.api_key}

            response = await self.client.post(url, json=request_data, params=params)

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])

                if candidates:
                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    finish_reason = candidates[0].get("finishReason", "unknown")

                    return {
                        "success": True,
                        "content": content,
                        "model": model,
                        "finish_reason": finish_reason,
                        "usage": result.get("usageMetadata", {}),
                    }
                else:
                    return {
                        "error": "No candidates in Gemini response",
                        "full_response": result,
                    }
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", {}).get("message", error_msg)
                except Exception:
                    pass

                logger.error(f"Gemini API error: {error_msg}")

                return {
                    "error": f"Gemini API error: {error_msg}",
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"Gemini API exception: {e}")
            return {"error": f"Gemini API exception: {e!s}"}

    async def generate_with_system_instruction(
        self,
        prompt: str,
        system_instruction: str,
        conversation_history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Gemini API 호출 with system_instruction (Gem 에뮬레이션용)

        Args:
            prompt: 사용자 메시지
            system_instruction: 시스템 인스트럭션 (Gem 동작 정의)
            conversation_history: 이전 대화 기록 [{"role": "user/model", "content": "..."}]
            **kwargs: 추가 설정 (model, temperature, max_tokens 등)

        Returns:
            dict with success, content, model, finish_reason, usage
        """
        if not self.available or not self.client:
            return {
                "error": "Gemini API not available",
                "fallback": "[Gemini Unavailable] System instruction response",
            }

        try:
            model = kwargs.get("model", "gemini-1.5-flash")
            url = f"{self.base_url}/v1beta/models/{model}:generateContent"

            # Build contents array with conversation history
            contents: list[dict[str, Any]] = []

            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

            # Add current user message
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            request_data: dict[str, Any] = {
                "contents": contents,
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 2048),
                    "topP": 0.95,
                    "topK": 40,
                },
            }

            params = {"key": self.api_key}

            response = await self.client.post(url, json=request_data, params=params)

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])

                if candidates:
                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    finish_reason = candidates[0].get("finishReason", "unknown")

                    return {
                        "success": True,
                        "content": content,
                        "model": model,
                        "finish_reason": finish_reason,
                        "usage": result.get("usageMetadata", {}),
                    }
                else:
                    return {"error": "No candidates in Gemini response"}
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", {}).get("message", error_msg)
                except Exception:
                    pass

                return {
                    "error": f"Gemini API error: {error_msg}",
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"Gemini API system instruction exception: {e}")
            return {"error": f"Gemini API exception: {e!s}"}

    async def generate_with_context(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """
        대화 맥락을 포함한 생성
        """
        if not self.available or not self.client:
            return {
                "error": "Gemini API not available",
                "fallback": "[Gemini Unavailable] Context-based response",
            }

        try:
            model = kwargs.get("model", "gemini-1.5-pro")
            url = f"{self.base_url}/v1beta/models/{model}:generateContent"

            # 메시지 변환 (OpenAI 스타일 → Gemini 스타일)
            contents: list[dict[str, Any]] = []
            current_content: dict[str, list[dict[str, str]]] = {"parts": []}

            for msg in messages:
                role = msg["role"]
                content = msg["content"]

                if role == "system":
                    # 시스템 메시지를 첫 사용자 메시지에 추가
                    if not contents:
                        current_content["parts"].append({"text": f"System: {content}\n\n"})
                    else:
                        current_content["parts"][-1]["text"] += f"\n\nSystem: {content}"
                elif role == "user" or role == "assistant":
                    if current_content["parts"]:
                        contents.append(current_content)
                        current_content = {"parts": []}
                    current_content["parts"].append({"text": content})

            if current_content["parts"]:
                contents.append(current_content)

            request_data = {
                "contents": contents,
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 2048),
                    "topP": 0.95,
                    "topK": 40,
                },
            }

            params = {"key": self.api_key}

            response = await self.client.post(url, json=request_data, params=params)

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])

                if candidates:
                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    finish_reason = candidates[0].get("finishReason", "unknown")

                    return {
                        "success": True,
                        "content": content,
                        "model": model,
                        "finish_reason": finish_reason,
                        "usage": result.get("usageMetadata", {}),
                    }
                else:
                    return {"error": "No candidates in Gemini response"}
            else:
                error_msg = response.text
                return {
                    "error": f"Gemini API error: {error_msg}",
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"Gemini API context exception: {e}")
            return {"error": f"Gemini API exception: {e!s}"}

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
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-2.0-flash-exp",
            "gemini-pro",
            "gemini-pro-vision",
        ]

    def get_cost_estimate(self, tokens: int) -> float:
        """비용 추정 (달러)"""
        # Gemini 비용 (2024년 기준)
        # Gemini 1.5 Pro: $0.00125/M tokens input, $0.005/M tokens output
        input_cost_per_million = 1.25
        output_cost_per_million = 5.0

        # 대략적인 추정: 입력 토큰의 20%가 출력 토큰
        input_tokens = tokens * 0.8
        output_tokens = tokens * 0.2

        cost = (input_tokens / 1_000_000) * input_cost_per_million + (
            output_tokens / 1_000_000
        ) * output_cost_per_million

        return cost


# 글로벌 인스턴스
gemini_api = GeminiAPIWrapper()


if __name__ == "__main__":
    # 테스트
    async def test_gemini_api() -> None:
        print("🤖 Gemini API Wrapper 테스트")
        print("=" * 50)

        if not gemini_api.is_available():
            print("❌ Gemini API 키가 설정되지 않음")
            print("   환경변수 GEMINI_API_KEY를 설정해주세요")
            return

        test_prompt = "안녕하세요! 당신은 누구인가요?"

        print(f"🔍 테스트 프롬프트: {test_prompt}")

        try:
            result = await gemini_api.generate(test_prompt, max_tokens=200)

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

        await gemini_api.close()

    asyncio.run(test_gemini_api())
