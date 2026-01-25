"""AI API Clients for Diagram Generation

Handles AI model API calls for diagram structure generation.

Trinity Score: 眞 90% | 善 95% | 美 85%
- 眞 (Truth): Reliable API communication
- 善 (Goodness): Error handling and security
- 美 (Beauty): Clean response parsing
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AIClientManager:
    """AI API 클라이언트 매니저.

    다양한 AI 모델과의 통신을 관리합니다.
    """

    async def call_ai_api(self, prompt: str, ai_model: str) -> str | None:
        """AI API 호출.

        Args:
            prompt: 프롬프트
            ai_model: 모델 선택

        Returns:
            AI 응답 또는 None
        """
        try:
            if ai_model == "claude":
                return await self._call_claude_api(prompt)
            elif ai_model == "gpt4":
                return await self._call_gpt4_api(prompt)
            elif ai_model == "local":
                return await self._call_local_ai(prompt)
            else:
                logger.error(f"Unsupported AI model: {ai_model}")
                return None

        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return None

    async def _call_claude_api(self, prompt: str) -> str | None:
        """Claude API 호출.

        Args:
            prompt: 프롬프트

        Returns:
            Claude 응답
        """
        try:
            import os

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not found, skipping Claude API")
                return None

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-sonnet-20240229",
                        "max_tokens": 2048,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    logger.error(f"Claude API error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Claude API call error: {e}")
            return None

    async def _call_gpt4_api(self, prompt: str) -> str | None:
        """GPT-4 API 호출 (미구현 - 필요시 구현).

        Args:
            prompt: 프롬프트

        Returns:
            GPT-4 응답
        """
        logger.warning("GPT-4 API not implemented yet")
        return None

    async def _call_local_ai(self, prompt: str) -> str | None:
        """로컬 AI 호출 (미구현 - 필요시 구현).

        Args:
            prompt: 프롬프트

        Returns:
            로컬 AI 응답
        """
        logger.warning("Local AI not implemented yet")
        return None

    def parse_ai_response(self, response: str, diagram_type: str) -> dict[str, Any] | None:
        """AI 응답을 파싱하여 구조 생성.

        Args:
            response: AI 응답 텍스트
            diagram_type: 다이어그램 유형

        Returns:
            파싱된 구조 또는 None
        """
        try:
            # JSON 추출 (마크다운 코드 블록 내 JSON)
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response.strip()

            structure = json.loads(json_str)

            # 구조 검증 및 기본값 설정
            if "nodes" not in structure:
                structure["nodes"] = []

            if "connections" not in structure:
                structure["connections"] = []

            if "title" not in structure:
                structure["title"] = f"{diagram_type.title()} Diagram"

            if "layout" not in structure:
                structure["layout"] = {
                    "type": "hierarchical",
                    "direction": "top-bottom",
                }

            return structure

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"AI response parsing error: {e}")
            return None
