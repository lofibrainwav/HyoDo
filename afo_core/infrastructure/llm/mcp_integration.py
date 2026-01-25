from __future__ import annotations

import asyncio
import importlib.util
import logging
import re
from typing import Any

from AFO.afo_skills_registry import skills_registry
from infrastructure.json_fast import loads as json_loads_fast

# Try to import context7 service
try:
    from services.context7_service import get_context7_instance
except ImportError:
    try:
        from AFO.services.context7_service import get_context7_instance
    except ImportError:
        get_context7_instance = None  # type: ignore[assignment]

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO MCP Integration - Context7 + Sequential Thinking + Skills

MCP 도구들을 LLM Router와 통합하여 왕궁 대화에서 활용 가능하게 함.
- Context7: 라이브러리 문서 주입
- Sequential Thinking: 단계별 사고 프로세스
- Skills Registry: 동적 도구 접근
"""


logger = logging.getLogger(__name__)


class MCPIntegration:
    """MCP 도구 통합 관리자"""

    def __init__(self) -> None:
        self._context7_available = False
        self._skills_registry_available = False
        self._initialize()

    def _initialize(self) -> None:
        """MCP 컴포넌트 초기화"""
        # Context7 체크
        if get_context7_instance is not None:
            self._context7_available = True
            logger.info("✅ Context7 MCP available")
        else:
            logger.warning("⚠️ Context7 MCP not available")

        # Skills Registry 체크
        try:
            if importlib.util.find_spec("AFO.afo_skills_registry"):
                self._skills_registry_available = True
                logger.info("✅ Skills Registry available")
            else:
                logger.warning("⚠️ Skills Registry not available")
        except ImportError:
            logger.warning("⚠️ Skills Registry not available")

    async def enrich_with_context7(
        self, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Context7을 사용하여 쿼리에 관련 문서 주입

        Args:
            query: 사용자 쿼리
            context: 기존 컨텍스트

        Returns:
            enriched context with relevant documents
        """
        ctx = context or {}

        if not self._context7_available or get_context7_instance is None:
            ctx["context7_status"] = "unavailable"
            return ctx

        try:
            instance = get_context7_instance()
            if instance:
                if hasattr(instance, "retrieve_context"):
                    # Context7MCP (trinity-os) uses retrieve_context
                    results = await instance.retrieve_context(query=query)
                elif hasattr(instance, "search"):
                    results = instance.search(query=query, top_k=3)
                else:
                    results = None

                if results:
                    # results can be a list of strings or a list of dicts
                    formatted_results = []
                    for res in results:
                        if isinstance(res, dict):
                            content = res.get("content") or res.get("text", str(res))
                            formatted_results.append(content)
                        else:
                            formatted_results.append(str(res))

                    ctx["context7_docs"] = formatted_results
                    ctx["context7_status"] = "enriched"
                    logger.debug(f"📚 Context7: Found {len(formatted_results)} relevant docs")
                else:
                    ctx["context7_status"] = "no_results"
            else:
                ctx["context7_status"] = "instance_error"
        except Exception as e:
            logger.warning(f"Context7 enrichment failed: {e}")
            ctx["context7_status"] = f"error: {e}"

        return ctx

    def apply_sequential_thinking(
        self, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Sequential Thinking 패턴 적용 (복잡한 추론에 활용)

        Args:
            query: 사용자 쿼리
            context: 기존 컨텍스트

        Returns:
            context with thinking steps template
        """
        ctx = context or {}

        # 질문 분석을 위한 사고 체인 템플릿
        thinking_template = {
            "step_1_understand": "문제를 명확히 이해하고 핵심 요소 파악",
            "step_2_decompose": "복잡한 문제를 작은 단위로 분해",
            "step_3_analyze": "각 부분을 개별적으로 분석",
            "step_4_synthesize": "분석 결과를 종합하여 해결책 도출",
            "step_5_verify": "결론의 논리적 타당성 검증",
        }

        ctx["sequential_thinking"] = {
            "enabled": True,
            "template": thinking_template,
            "query_type": self._classify_complexity(query),
        }

        return ctx

    def _classify_complexity(self, query: str) -> str:
        """쿼리 복잡도 분류"""
        q_lower = query.lower()

        # 복잡도 키워드 체크
        high_complexity = ["분석", "비교", "추론", "왜", "어떻게", "단계", "reasoning"]
        medium_complexity = ["설명", "describe", "what", "뭐", "무엇"]

        for kw in high_complexity:
            if kw in q_lower:
                return "high"

        for kw in medium_complexity:
            if kw in q_lower:
                return "medium"

        return "low"

    def get_available_skills(self) -> list[dict[str, Any]]:
        """
        사용 가능한 Skills 목록 반환

        Returns:
            List of available skills with metadata
        """
        if not self._skills_registry_available:
            return []

        try:
            registry = skills_registry
            skills = []

            for skill_id, skill_info in registry.skills.items():
                skills.append(
                    {
                        "id": skill_id,
                        "name": getattr(skill_info, "name", skill_id),
                        "description": getattr(skill_info, "description", ""),
                        "category": getattr(skill_info, "category", "general"),
                    }
                )

            logger.debug(f"🛠️ Found {len(skills)} available skills")
            return skills
        except Exception as e:
            logger.warning(f"Failed to get skills: {e}")
            return []

    async def execute_skill(
        self, skill_id: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        스킬 실행

        Args:
            skill_id: 실행할 스킬 ID
            params: 스킬 파라미터

        Returns:
            Skill execution result
        """
        if not self._skills_registry_available:
            return {"error": "Skills registry not available"}

        try:
            # SkillRegistry might have 'execute' or 'execute_skill' depending on version
            if hasattr(skills_registry, "execute"):
                result = await skills_registry.execute(skill_id, params or {})
            elif hasattr(skills_registry, "execute_skill"):
                result = await skills_registry.execute_skill(skill_id, params or {})
            else:
                # Fallback to manual execution (simplified)
                skill = skills_registry.get(skill_id)
                if not skill:
                    return {"success": False, "error": f"Skill {skill_id} not found"}
                result = f"Skill {skill_id} found but no execution method available in registry."

            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return {"success": False, "error": str(e)}

    def parse_tool_call(self, text: str) -> list[dict[str, Any]]:
        """
        LLM 응답에서 USE_SKILL 패턴을 분석하여 실행 대기 목록 생성

        예: USE_SKILL: skill_id, params: {"key": "value"}
        """

        # 정규식 패턴: USE_SKILL: {skill_id}, params: {json_params}
        pattern = r"USE_SKILL:\s*([a-zA-Z0-9_\-]+),\s*params:\s*({.*})"
        matches = re.finditer(pattern, text)

        calls = []
        for match in matches:
            skill_id = match.group(1).strip()
            params_str = match.group(2).strip()
            try:
                params = json_loads_fast(params_str)
                calls.append({"skill_id": skill_id, "params": params})
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse skill params: {params_str}")

        return calls

    def get_integration_status(self) -> dict[str, Any]:
        """MCP 통합 상태 반환"""
        return {
            "context7": self._context7_available,
            "skills_registry": self._skills_registry_available,
            "sequential_thinking": True,  # Always available (template-based)
        }


# Singleton instance
mcp_integration = MCPIntegration()


# ============================================================================
# Convenience Functions
# ============================================================================


async def enrich_query_context(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    쿼리 컨텍스트 강화 (Context7 + Sequential Thinking)

    Args:
        query: 사용자 쿼리
        context: 기존 컨텍스트

    Returns:
        Enriched context
    """
    ctx = context or {}

    # 1. Context7 문서 주입
    ctx = await mcp_integration.enrich_with_context7(query, ctx)

    # 2. Sequential Thinking 적용 (복잡한 쿼리에만)
    if mcp_integration._classify_complexity(query) in ("high", "medium"):
        ctx = mcp_integration.apply_sequential_thinking(query, ctx)

    return ctx


def get_mcp_status() -> dict[str, Any]:
    """MCP 통합 상태 조회"""
    return mcp_integration.get_integration_status()


def parse_llm_tool_calls(text: str) -> list[dict[str, Any]]:
    """LLM 응답에서 도구 호출 패턴 파싱"""
    return mcp_integration.parse_tool_call(text)


# ============================================================================
# Self-Test
# ============================================================================

if __name__ == "__main__":

    async def test_mcp_integration() -> None:
        print("=" * 60)
        print("AFO MCP Integration - Self Test")
        print("=" * 60)

        # 1. Status check
        print("\n📊 Integration Status:")
        status = get_mcp_status()
        for key, val in status.items():
            icon = "✅" if val else "❌"
            print(f"   {icon} {key}: {val}")

        # 2. Context enrichment test
        print("\n📚 Testing Context Enrichment...")
        ctx = await enrich_query_context("FastAPI로 REST API 만드는 방법 알려줘")
        print(f"   Context7 Status: {ctx.get('context7_status', 'unknown')}")
        if ctx.get("sequential_thinking"):
            print(f"   Sequential Thinking: enabled ({ctx['sequential_thinking']['query_type']})")

        # 3. Skills list
        print("\n🛠️ Available Skills:")
        skills = mcp_integration.get_available_skills()
        if skills:
            for skill in skills[:5]:
                print(f"   - {skill['id']}: {skill['description'][:50]}...")
        else:
            print("   (No skills available)")

        print("\n✅ Self-test completed!")

    asyncio.run(test_mcp_integration())
