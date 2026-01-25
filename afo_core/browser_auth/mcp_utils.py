# Trinity Score: 96.0 (Phase 30 MCP Utils Refactoring)
"""MCP Browser Auth Utilities - Helper Functions"""

import asyncio
import json
import os
import sys
from typing import Any

from AFO.config.settings import get_settings

from .mcp_auth import MCPIntegratedAuth


async def mcp_auth_experiment(
    url: str = "https://chat.openai.com/auth/login",
    prompt: str = "ChatGPT 로그인 테스트 생성해, MCP로 페이지 탐색",
    llm_provider: str = "anthropic",
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    MCP 통합 인증 실험 헬퍼 함수

    Args:
        url: 대상 URL
        prompt: 테스트 생성 프롬프트
        llm_provider: LLM 제공자 ("anthropic" 또는 "openai")
        api_key: API 키

    Returns:
        실행 결과
    """
    mcp_auth = MCPIntegratedAuth(llm_provider=llm_provider, api_key=api_key)
    return await mcp_auth.execute_mcp_auth_flow(url, prompt)


def main() -> None:
    """메인 엔트리포인트"""
    # Phase 2-4: settings 사용
    try:
        settings = get_settings()
        api_key = settings.ANTHROPIC_API_KEY
    except ImportError:
        try:
            settings = get_settings()
            api_key = settings.ANTHROPIC_API_KEY
        except ImportError:
            api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY 환경변수를 설정해주세요")
        print("   또는 OPENAI_API_KEY를 사용하려면 llm_provider='openai' 설정")
        sys.exit(1)

    result = asyncio.run(mcp_auth_experiment(llm_provider="anthropic", api_key=api_key))

    print("\n" + "=" * 70)
    print("📊 MCP 통합 실험 결과")
    print("=" * 70)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
