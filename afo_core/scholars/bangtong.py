from __future__ import annotations

import asyncio
import logging
from typing import Any

from AFO.llms.codex_cli import CodexCLIWrapper, codex_cli

# Trinity Score: 90.0 (Established by Chancellor)
"""Bangtong (Codex) - The Implementation Scholar (Implementation & Prototyping)

Identity:
- Name: Bangtong (Pang Tong)
- Role: Implementation, Execution, Prototyping
- Specialization: Python, FastAPI, Next.js, Refactoring
- Personality: Practical, Efficient, Solution-oriented (The "Phoenix Fledgling")

Responsibilities:
1. Translate architectural designs into working code.
2. Generate boilerplate and scaffold structures.
3. Optimize implementation details for performance.
"""


# [정기구독] CLI 기반 연동 (API 키 불필요)

logger = logging.getLogger(__name__)


class BangtongScholar:
    """방통 (Bangtong) - 구현 및 프로토타이핑 담당 학자
    Codex CLI 기반의 코딩 전문가 (정기구독)
    """

    SYSTEM_PROMPT = """
    당신은 AFO Kingdom의 집현전 학자 '방통(Bangtong)'입니다.
    당신의 주 임무는 '구현(Implementation)'과 '실행(Execution)'입니다.

    [핵심 기술 스택]
    - 언어: Python 3.12+, TypeScript
    - 프레임워크: FastAPI, Next.js 14+ (App Router)
    - AI 프레임워크 (전문가): LangChain, LangGraph, CrewAI, AutoGen

    [원칙]
    1. 작동하는 코드: 이론보다 실제 작동하는 코드를 우선합니다.
    2. 효율성: 불필요한 복잡성을 제거하고 간결한 구현을 지향합니다.
    3. 모던 스택: 최신 AI 프레임워크의 Best Practice를 따릅니다.
    4. 타입 안전성: 모든 Python 코드에 Type hint를 적용합니다.

    당신은 제갈량(전략)의 설계를 바탕으로 실질적인 결과물을 만들어냅니다. 특히 복잡한 에이전트 그래프나 멀티 에이전트 협업 체계를 코드로 구현하는 데 탁월한 능력을 발휘합니다.
    """

    def __init__(self, api_wrapper: CodexCLIWrapper | None = None) -> None:
        self.api = api_wrapper or codex_cli
        self.model = "codex-cli"  # CLI 모드 사용

    async def implement(self, request: str, context: dict[str, Any] | None = None) -> str:
        """요구사항을 코드로 구현"""
        context_prompt = ""
        if context:
            context_prompt = f"\n[Context]\n{context}"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"다음 요구사항을 구현하시오:\n{request}{context_prompt}",
            },
        ]

        logger.info(f"📜 [Bangtong] Implementing: {request[:50]}...")

        result = await self.api.generate_with_context(
            messages=messages,
            model=self.model,
            temperature=0.2,  # Code generation needs low temperature
        )

        if result.get("success"):
            return str(result["content"])
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"❌ [Bangtong] Implementation failed: {error}")
            return f"구현 실패: {error}"

    async def review_implementation(self, code: str) -> str:
        """구현 코드 리뷰 및 최적화 제안"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"다음 코드를 리뷰하고 최적화 방안을 제시하시오:\n```\n{code}\n```",
            },
        ]

        result = await self.api.generate_with_context(
            messages=messages, model=self.model, temperature=0.4
        )

        if result.get("success"):
            return str(result["content"])
        else:
            return f"리뷰 실패: {result.get('error')}"


# Singleton Instance
bangtong = BangtongScholar()

if __name__ == "__main__":

    async def test_bangtong():
        print("🐥 Bangtong Scholar Test")

        # Test Implementation
        code_req = "Python으로 간단한 Fibonacci 수열 생성기를 Iterator로 구현해줘."
        response = await bangtong.implement(code_req)
        print(f"\n[Request]: {code_req}")
        print(f"[Response]:\n{response[:200]}...\n")

    asyncio.run(test_bangtong())
