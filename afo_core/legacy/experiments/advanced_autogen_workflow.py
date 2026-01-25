from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional

from afo_soul_engine.langgraph.twin_dragon_graph import (
    LANGGRAPH_AVAILABLE,
    run_langgraph_state,
    run_twin_dragon_router,
    seed_trinity,
)
from autogen import AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent
from autogen.code_utils import create_function_tool

# Trinity Score: 90.0 (Established by Chancellor)
"""Advanced AutoGen multi-agent workflow (Option C Ready).

This script reuses the CREW_MODE pattern so we can dry-run everything offline
without API keys, then flip to CREW_MODE=online + CLI wallet for the live
Twin Dragon run. In offline mode we simply emit deterministic mock output so
pipelines/tests never fail.
"""


try:
    AUTOGEN_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    AUTOGEN_AVAILABLE = False


# CREW_MODE integration (offline by default)
CREW_MODE = os.getenv("CREW_MODE", "offline").lower()


def offline_summary() -> dict[str, Any]:
    """Fallback payload when AutoGen/keys are unavailable."""
    return {
        "status": "offline-mock",
        "message": "CREW_MODE!=online or AutoGen not installed. Returning mock data.",
        "conversation": [
            {"role": "user", "content": "Research AI trends 2025 using tools"},
            {
                "role": "assistant",
                "content": "Mock response: summarized 3 trends (Hybrid RAG, Twin Dragon, Trinity Ops).",
            },
        ],
    }


def build_llm_config() -> dict[str, Any] | None:
    """Create AutoGen llm_config when CREW_MODE=online."""
    if CREW_MODE != "online":
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY missing; switch to CREW_MODE=offline or export a valid key.")
        return None

    model = os.getenv("AUTOGEN_MODEL", "gpt-4o-mini")
    return {"config_list": [{"model": model, "api_key": api_key}]}


def create_search_tool() -> None:
    """Define a simple search tool usable by both offline/online flows."""

    def search_tool(query: str) -> str:
        if CREW_MODE == "online":
            return f"[search] live lookup for: {query}"
        return f"[search-mock] offline lookup for: {query}"

    if not AUTOGEN_AVAILABLE:
        return None, search_tool

    tool = create_function_tool(
        search_tool,
        name="search",
        description="Perform knowledge searches across AFO knowledge bases.",
    )
    return tool, search_tool


def create_twin_dragon_tool(default_priority: str = "balanced") -> None:
    """Expose the Twin Dragon router as an AutoGen function tool."""

    def twin_dragon_router(query: str, priority: str = "balanced") -> str:
        routed_priority = priority or default_priority
        if CREW_MODE != "online":
            payload = {
                "success": True,
                "response": f"[router-mock] {query}",
                "routing": {
                    "provider": "ollama",
                    "model": "qwen3-vl:8b",
                    "priority": routed_priority,
                    "reasoning": "CREW_MODE offline mock",
                },
            }
            return json.dumps(payload, ensure_ascii=False)

        result = run_twin_dragon_router(query, routed_priority)
        return json.dumps(result, ensure_ascii=False)

    if not AUTOGEN_AVAILABLE:
        return None, twin_dragon_router

    tool = create_function_tool(
        twin_dragon_router,
        name="twin_dragon_router",
        description="Invoke the Twin Dragon LLM router (Ollama → API fallback).",
    )
    return tool, twin_dragon_router


def create_langgraph_tool(default_priority: str = "balanced") -> None:
    """Expose the LangGraph Twin Dragon state machine as a tool."""

    def langgraph_state(query: str, priority: str = "balanced") -> str:
        routed_priority = priority or default_priority
        if CREW_MODE != "online":
            payload = {
                "status": "offline-mock",
                "query": query,
                "provider": "ollama",
                "trinity_focus": seed_trinity(routed_priority),
                "priority": routed_priority,
                "message": "LangGraph skipped because CREW_MODE!=online.",
            }
            return json.dumps(payload, ensure_ascii=False)

        if not LANGGRAPH_AVAILABLE:
            payload = {
                "status": "langgraph-missing",
                "message": "langgraph not installed; returning mock route.",
                "query": query,
            }
            return json.dumps(payload, ensure_ascii=False)

        result = run_langgraph_state(query, priority=routed_priority)
        return json.dumps(result, ensure_ascii=False)

    if not AUTOGEN_AVAILABLE:
        return None, langgraph_state

    tool = create_function_tool(
        langgraph_state,
        name="langgraph_state",
        description="Run the Twin Dragon LangGraph workflow for the given query.",
    )
    return tool, langgraph_state


def run_autogen_workflow(
    llm_config: dict[str, Any],
    human_mode: str,
    prompt: str,
    default_priority: str,
) -> dict[str, Any]:
    """Execute the AutoGen conversation."""
    search_func_tool, search_callable = create_search_tool()
    router_tool, router_callable = create_twin_dragon_tool(default_priority)
    langgraph_tool, langgraph_callable = create_langgraph_tool(default_priority)

    function_map = {}
    for name, fn in [
        ("search", search_callable),
        ("twin_dragon_router", router_callable),
        ("langgraph_state", langgraph_callable),
    ]:
        if fn:
            function_map[name] = fn

    assistant_functions = [
        tool for tool in [search_func_tool, router_tool, langgraph_tool] if tool is not None
    ]

    user_proxy = UserProxyAgent(
        name="HumanProxy",
        human_input_mode=human_mode,
        code_execution_config=False,
        function_map=function_map,
    )

    assistant = AssistantAgent(
        name="AutoGenStrategist",
        llm_config=llm_config,
        system_message=(
            "You are an enterprise AI strategist. Use the provided search, router, "
            "and LangGraph tools when needed and end your final response with 'TERMINATE'."
        ),
        functions=assistant_functions or None,
    )

    groupchat = GroupChat(
        agents=[user_proxy, assistant],
        messages=[],
        max_round=12,
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    user_proxy.initiate_chat(manager, message=prompt)
    conversation = manager.groupchat.messages
    return {
        "status": "success",
        "conversation": conversation,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advanced AutoGen workflow runner.")
    parser.add_argument(
        "--prompt",
        type=str,
        default="Research AI trends 2025 using tools",
        help="Seed prompt for the AutoGen conversation",
    )
    parser.add_argument(
        "--human-mode",
        type=str,
        default=None,
        choices=["ALWAYS", "NEVER", "TERMINATE"],
        help="Override AutoGen human_input_mode (defaults to interactive-aware setting)",
    )
    parser.add_argument(
        "--priority",
        type=str,
        default="balanced",
        choices=["speed", "balanced", "high", "ultra"],
        help="Twin Dragon / LangGraph priority preset passed to the router tools.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    human_mode = args.human_mode

    if human_mode is None:
        # Default: ALWAYS if tty, otherwise NEVER (for CI pipelines)
        human_mode = "ALWAYS" if sys.stdin.isatty() else "NEVER"

    llm_config = build_llm_config()
    if not AUTOGEN_AVAILABLE or not llm_config:
        payload = offline_summary()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    # propagate priority to prompt for quick awareness
    prompt = f"[priority={args.priority}] {args.prompt}"

    try:
        payload = run_autogen_workflow(
            llm_config=llm_config,
            human_mode=human_mode,
            prompt=prompt,
            default_priority=args.priority,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        payload = {"status": "error", "message": str(exc)}

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
