import json
import logging
from typing import TYPE_CHECKING, Any

from AFO.afo_skills_registry import register_core_skills
from AFO.scholars.libraries.obsidian_bridge import LocalObsidianBridge
from AFO.services.mcp_stdio_client import call_tool, list_tools

if TYPE_CHECKING:
    from .sages import ThreeSages

logger = logging.getLogger(__name__)


class RoyalTools:
    """영덕이 사용하는 왕실 도구 모음"""

    def __init__(self, sages: "ThreeSages") -> None:
        self.sages = sages

    async def document_code(self, code: str) -> str:
        """코드 문서화 (사마휘 담당)"""
        prompt = f"다음 코드에 대한 상세한 문서(Docstring/README)를 작성하시오:\n```\n{code}\n```"
        return await self.sages.consult_samahwi(prompt)

    async def summarize_log(self, logs: str) -> str:
        """로그 요약 (사마휘 담당)"""
        prompt = f"다음 로그/텍스트를 핵심 위주로 요약하시오:\n{logs}"
        return await self.sages.consult_samahwi(prompt)

    async def security_scan(self, content: str) -> str:
        """보안 스캔 (사마휘 담당)"""
        prompt = (
            f"다음 내용에서 API 키, 비밀번호, 개인정보 등 민감 정보가 있는지 확인하시오:\n{content}"
        )
        return await self.sages.consult_samahwi(prompt)

    async def use_tool(self, tool_name: str, **kwargs: Any) -> str:
        """왕실 도구 사용 (Royal Tool Usage)"""
        registry = register_core_skills()
        skill = registry.get(tool_name)

        if not skill:
            return f"❌ [Yeongdeok] Tool '{tool_name}' not found in the Royal Arsenal."

        logger.info(f"🛠️ [Yeongdeok] Using tool: {skill.name} ({tool_name})...")

        if tool_name == "skill_012_mcp_tool_bridge":
            return self._use_mcp_bridge(**kwargs)
        elif tool_name == "skill_013_obsidian_librarian":
            return self._use_obsidian_bridge(**kwargs)

        return f"✅ [Yeongdeok] Tool '{skill.name}' execution completed.\n(Result placeholder)"

    def _use_mcp_bridge(self, **kwargs: Any) -> str:
        try:
            action = (kwargs.get("action") or "list_tools").strip()
            server_name = (kwargs.get("server") or "afo-ultimate-mcp").strip()

            if action == "list_tools":
                tools = list_tools(server_name)
                if not tools:
                    return f"⚠️ [Yeongdeok] MCP server '{server_name}' returned no tools."
                return f"✅ [Yeongdeok] MCP tools ({server_name}): " + ", ".join(sorted(tools))

            if action == "retrieve_context":
                query = kwargs.get("query") or kwargs.get("text") or "AFO Architecture"
                resp = call_tool(
                    server_name,
                    tool_name="retrieve_context",
                    arguments={"query": str(query), "domain": "technical"},
                )
                return json.dumps(resp.get("result", {}), ensure_ascii=False)[:2000]

            if action == "sequential_thinking":
                thought = kwargs.get("thought") or "Proceed step by step."
                resp = call_tool(
                    server_name,
                    tool_name="sequential_thinking",
                    arguments={
                        "thought": str(thought),
                        "thought_number": int(kwargs.get("thought_number") or 1),
                        "total_thoughts": int(kwargs.get("total_thoughts") or 1),
                        "next_thought_needed": bool(
                            kwargs.get("next_thought_needed")
                            if kwargs.get("next_thought_needed") is not None
                            else False
                        ),
                    },
                )
                return json.dumps(resp.get("result", {}), ensure_ascii=False)[:2000]

            # Generic tool call
            tool = kwargs.get("tool") or kwargs.get("tool_name")
            if not tool:
                return f"❌ [Yeongdeok] MCP action '{action}' requires 'tool'"
            arguments = kwargs.get("arguments")
            if arguments is not None and not isinstance(arguments, dict):
                return "❌ [Yeongdeok] MCP 'arguments' must be an object"

            resp = call_tool(
                server_name,
                tool_name=str(tool),
                arguments=arguments or {},
            )
            return json.dumps(resp.get("result", {}), ensure_ascii=False)[:2000]
        except Exception as e:
            return f"Error using MCP Bridge: {e}"

    def _use_obsidian_bridge(self, **kwargs: Any) -> str:
        try:
            bridge = LocalObsidianBridge()
            action = kwargs.get("action", "append_daily_log")

            if action == "write_note":
                res = bridge.write_note(
                    kwargs.get("note_path", "untitled.md"),
                    kwargs.get("content", ""),
                    kwargs.get("metadata", {}),
                )
            elif action == "read_note":
                res = bridge.read_note(kwargs.get("note_path", ""))
            elif action == "append_daily_log":
                res = bridge.append_daily_log(
                    kwargs.get("content", ""), kwargs.get("tag", "general")
                )
            else:
                return f"❌ [Yeongdeok] Unknown archival action: {action}"

            if res.get("success"):
                return f"✅ [Yeongdeok] Archived to Royal Library: {res.get('path', 'unknown')}"
            else:
                return f"⚠️ [Yeongdeok] Archival Failed: {res.get('error')}"
        except Exception as e:
            return f"❌ [Yeongdeok] Hand of the King Error: {e}"
