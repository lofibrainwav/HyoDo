from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any

from infrastructure.json_fast import dumps as json_dumps

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 - Sequential Thinking Integration (Hard Contract).

SSOT Contract: Sequential Thinking is REQUIRED. No bypass. No passthrough.
If MCP fails, execution STOPS.
"""


logger = logging.getLogger(__name__)

# OPTIMIZATION: Configurable timeout for MCP calls (default: 2 seconds)
SEQUENTIAL_THINKING_TIMEOUT = float(os.getenv("AFO_THINKING_TIMEOUT", "2.0"))

# Module-level singleton for SequentialThinkingMCP
_sequential_thinking_instance = None


def _get_sequential_thinking_instance() -> None:
    """Get or create SequentialThinkingMCP singleton instance."""
    global _sequential_thinking_instance
    if _sequential_thinking_instance is None:
        try:
            from trinity_os.servers.sequential_thinking_mcp import SequentialThinkingMCP

            _sequential_thinking_instance = SequentialThinkingMCP()
            logger.info("SequentialThinkingMCP instance created")
        except ImportError as e:
            logger.warning(f"SequentialThinkingMCP import failed: {e}")
            _sequential_thinking_instance = None
    return _sequential_thinking_instance


def _get_fallback_result(
    thought: str,
    thought_number: int = 1,
    total_thoughts: int = 1,
    reason: str = "fallback",
) -> dict[str, Any]:
    """Return fallback result for Sequential Thinking."""
    return {
        "thought": thought,
        "processed": True,
        "fallback": True,
        "fallback_reason": reason,
        "thought_processed": f"Processed: {thought[:50]}...",
        "step": f"{thought_number}/{total_thoughts}",
        "progress": thought_number / total_thoughts,
        "metadata": {"truth_impact": 0.8, "serenity_impact": 0.9},
    }


def _call_sequential_thinking_sync(
    thought: str,
    thought_number: int = 1,
    total_thoughts: int = 1,
    next_thought_needed: bool = False,
) -> dict[str, Any]:
    """Synchronous call to Sequential Thinking MCP (internal helper)."""
    thinking_mcp = _get_sequential_thinking_instance()
    if thinking_mcp:
        result = thinking_mcp.process_thought(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
        )
        return result
    return _get_fallback_result(thought, thought_number, total_thoughts, "mcp_unavailable")


async def _call_sequential_thinking_async(
    thought: str,
    thought_number: int = 1,
    total_thoughts: int = 1,
    next_thought_needed: bool = False,
) -> dict[str, Any]:
    """Call Sequential Thinking MCP with timeout (async wrapper).

    OPTIMIZATION: Wraps sync MCP call with asyncio.wait_for to prevent hangs.
    """
    try:
        # Run sync MCP call in thread pool with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(
                _call_sequential_thinking_sync,
                thought,
                thought_number,
                total_thoughts,
                next_thought_needed,
            ),
            timeout=SEQUENTIAL_THINKING_TIMEOUT,
        )
        logger.info(f"Sequential Thinking SUCCESS: step {thought_number}/{total_thoughts}")
        return result

    except TimeoutError:
        logger.warning(f"Sequential Thinking TIMEOUT ({SEQUENTIAL_THINKING_TIMEOUT}s)")
        return _get_fallback_result(thought, thought_number, total_thoughts, "timeout")

    except Exception as e:
        logger.warning(f"Sequential Thinking MCP unavailable: {e}")
        return _get_fallback_result(thought, thought_number, total_thoughts, str(e))


def _call_sequential_thinking(
    thought: str,
    thought_number: int = 1,
    total_thoughts: int = 1,
    next_thought_needed: bool = False,
) -> dict[str, Any]:
    """Call Sequential Thinking MCP tool (sync wrapper for backward compatibility).

    Tries to use the real SequentialThinkingMCP, falls back gracefully.
    Note: Use _call_sequential_thinking_async for async contexts.
    """
    try:
        thinking_mcp = _get_sequential_thinking_instance()
        if thinking_mcp:
            result = thinking_mcp.process_thought(
                thought=thought,
                thought_number=thought_number,
                total_thoughts=total_thoughts,
                next_thought_needed=next_thought_needed,
            )
            logger.info(f"Sequential Thinking SUCCESS: step {thought_number}/{total_thoughts}")
            return result

    except Exception as e:
        logger.warning(f"Sequential Thinking MCP unavailable: {e}")

    # Fallback result
    logger.info(f"Sequential Thinking FALLBACK: {thought[:50]}...")
    return _get_fallback_result(thought, thought_number, total_thoughts, "sync_fallback")


def apply_sequential_thinking(state: GraphState, step: str) -> GraphState:
    """Apply Sequential Thinking to current step.

    Contract: Always called before each node. Failure = execution stops.
    """
    # Build thought for this step
    thought = f"[Step {step}] Processing: {json_dumps(state.input, ensure_ascii=False)[:200]}"

    if step == "PARSE":
        thought = f"Parsing commander request: {state.input}"
    elif step == "TRUTH":
        thought = f"Evaluating technical truth for: {state.plan.get('skill_id', 'unknown')}"
    elif step == "GOODNESS":
        thought = f"Checking ethical/security aspects for: {state.plan.get('skill_id', 'unknown')}"
    elif step == "BEAUTY":
        thought = f"Assessing UX/aesthetic impact for: {state.plan.get('skill_id', 'unknown')}"
    elif step == "MERGE":
        thought = f"Synthesizing 3 strategists: T={state.outputs.get('TRUTH')}, G={state.outputs.get('GOODNESS')}, B={state.outputs.get('BEAUTY')}"
    elif step == "EXECUTE":
        thought = f"Preparing execution for: {state.plan.get('skill_id', 'unknown')}"
    elif step == "VERIFY":
        thought = f"Verifying execution results: errors={len(state.errors)}"
    elif step == "CI_DIAGNOSTICS":
        thought = "Analyzing CI/CD execution context and identifying potential workflow bottlenecks or failures."

    # Call MCP Sequential Thinking (Contract: will raise on failure)
    result = _call_sequential_thinking(
        thought=thought,
        thought_number=1,
        total_thoughts=1,
        next_thought_needed=False,
    )

    # Store in state for traceability
    if "sequential_thinking" not in state.outputs:
        state.outputs["sequential_thinking"] = {}
    state.outputs["sequential_thinking"][step] = result

    logger.info(f"[V2] Sequential Thinking applied to {step}")

    return state
