from __future__ import annotations

import asyncio
import logging

from AFO.api.compat import get_antigravity_control
from AFO.llms.claude_cli import ClaudeCLIWrapper, claude_cli
from AFO.skills.skill_019 import skill_019

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
# mypy: ignore-errors
"""
Jaryong (Claude) - The Logic Scholar (Logic Verification & Refactoring)

Identity:
- Name: Jaryong (Zhao Yun)
- Role: Logic Verification, Refactoring, Safety Audit
- Specialization: Logic Consistency, Edge Case Handling, Clean Code
- Personality: Calm, Loyal, Thorough, Defensive (The "Ever-Victorious General")

Responsibilities:
1. Verify logic of implemented code.
2. Identify potential edge cases and security flaws.
3. Suggest refactoring for better readability and maintainability.
"""


# [정기구독] CLI 기반 연동 (API 키 불필요)

# Start with mock/stub import, handle failure gracefully
try:
    pass  # Placeholder
except ImportError:
    skill_019 = None


logger = logging.getLogger(__name__)


class JaryongScholar:
    """
    자룡 (Jaryong) - 논리 검증 및 리팩터링 담당 학자
    Claude 3.5 Sonnet 기반의 논리 전문가
    """

    SYSTEM_PROMPT = """
    당신은 AFO Kingdom의 집현전 학자 '자룡(Jaryong)'입니다.
    당신의 주 임무는 '논리 검증(Logic Verification)'과 '리팩터링(Refactoring)'입니다.

    [핵심 검증 대상]
    - 로직: 비동기 흐름, 에지 케이스, 가독성
    - 복잡 체인: LangChain 흐름 제어, LangGraph 상태 관리 및 순환 고리 검토
    - 자동화: CrewAI/AutoGen 에이전트 간의 통신 논리 및 충돌 분석
    - 안전: 보안 취약점, 무한 루프 방지, 실시간 감사(audit)

    [원칙]
    1. 무결점: 사소한 논리적 오류나 엣지 케이스도 놓치지 않습니다. 특히 복잡한 AI 에이전트 시스템에서의 상태 전이를 철저히 검증합니다.
    2. 방어적: 입력값 검증과 예외 처리를 중요하게 생각합니다.
    3. 가독성: 코드는 읽기 쉬워야 하며, 명확한 변수명과 구조를 지향합니다.
    4. 안전제일: 보안 취약점이나 위험한 패턴을 감지하면 즉시 경고합니다.

    당신은 방통(구현)이 작성한 코드를 검토하고 더욱 견고하게 만듭니다. 특히 분산된 에이전트들의 협업 로직과 복잡한 기술 스택 간의 데이터 무결성을 검증하는 데 최고의 능력을 발휘합니다.
    """

    def __init__(self, api_wrapper: ClaudeCLIWrapper | None = None) -> None:
        self.api = api_wrapper or claude_cli
        self.model = "claude-code-cli"  # CLI 모드 사용
        self.antigravity = get_antigravity_control()
        self.knowledge_skill = skill_019

    def _check_governance(self, action: str, code_context: str = "") -> bool:
        """Central Governance Check"""
        if not self.antigravity:
            logger.warning("⚠️ [Jaryong] Governance control missing! Proceeding with CAUTION.")
            return True  # Fail open if system core missing (or fail closed depending on policy? Safe=Closed)
            # Let's Fail Closed for safety in Pure Antigravity
            # return False

        # 1. Flag Check
        if not self.antigravity.check_governance(f"scholar_{action}"):
            logger.warning(f"🛡️ [Jaryong] Action '{action}' blocked by Governance Flag.")
            return False

        # 2. Risk Brake (Simple Heuristic Check on Code)
        # In a real scenario, we might calculate trinity score here or use a specialized model
        # For now, quick keyword check as part of Governance
        if "eval(" in code_context or "exec(" in code_context:
            logger.error(
                "🛡️ [Jaryong] Risk Brake: High Risk Code Pattern Detected (eval/exec). Blocked."
            )
            return False

        return True

    async def retrieve_knowledge(self, query: str) -> str:
        """
        [Context7] Retrieve relevant knowledge context
        """
        if not self.knowledge_skill:
            return ""

        try:
            results = await self.knowledge_skill.query(query)
            return "\n".join(results)
        except Exception as e:
            logger.warning(f"⚠️ [Jaryong] RAG retrieval failed: {e}")
            return ""

    async def verify_logic(self, code: str, context: str | None = None) -> str:
        """
        코드 논리 검증 및 취약점 분석
        """
        # 0. Governance Check
        if not self._check_governance("jaryong", code):
            return "❌ [Blocked] Governance Denied: Verification Request Blocked."

        # 0.5 Retrieve Knowledge
        knowledge = await self.retrieve_knowledge("security performance style")

        request_msg = f"다음 코드의 논리적 결함과 잠재적 버그를 분석하시오:\n```python\n{code}\n```"
        if context:
            request_msg += f"\n\n[Context]\n{context}"

        if knowledge:
            request_msg += f"\n\n[Royal Library Guidelines]\n{knowledge}"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": request_msg},
        ]

        logger.info("🛡️ [Jaryong] Verifying logic...")

        result = await self.api.generate_with_context(
            messages=messages, model=self.model, temperature=0.1
        )

        if result.get("success"):
            return str(result["content"])
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"❌ [Jaryong] Verification failed: {error}")
            return f"검증 실패: {error}"

    async def suggest_refactoring(self, code: str) -> str:
        """
        리팩터링 제안 (Clean Code)
        """
        # 0. Governance Check
        if not self._check_governance("jaryong", code):
            return "❌ [Blocked] Governance Denied: Refactoring Request Blocked."

        request_context = ""
        knowledge = await self.retrieve_knowledge("style performance")
        if knowledge:
            request_context = f"\n\n[Royal Library Guidelines]\n{knowledge}"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"다음 코드를 더 깨끗하고 안전하게 리팩터링하시오:\n```python\n{code}\n```{request_context}",
            },
        ]

        result = await self.api.generate_with_context(
            messages=messages, model=self.model, temperature=0.3
        )

        if result.get("success"):
            return str(result["content"])
        else:
            return f"리팩터링 제안 실패: {result.get('error')}"


# Singleton Instance
jaryong = JaryongScholar()

if __name__ == "__main__":

    async def test_jaryong():
        print("🐉 Jaryong Scholar Test")

        # Test Verification
        buggy_code = """
def divide_numbers(a, b):
    return a / b
        """
        response = await jaryong.verify_logic(buggy_code)
        print(f"\n[Code]:\n{buggy_code}")
        print(f"[Analysis]:\n{response[:200]}...\n")

    asyncio.run(test_jaryong())
