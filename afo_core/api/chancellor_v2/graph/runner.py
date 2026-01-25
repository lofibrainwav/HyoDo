from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from AFO.api.chancellor_v2.context7 import (
    inject_context,
    inject_context_async,
    inject_kingdom_dna,
)
from AFO.api.chancellor_v2.thinking import (
    _call_sequential_thinking_async,
    apply_sequential_thinking,
)
from AFO.config.settings import get_settings
from infrastructure.json_fast import dumps as json_dumps

from .state import GraphState
from .store import append_event, save_checkpoint

# Orchestrator import (lazy to avoid circular imports)
_orchestrator = None


def _get_orchestrator() -> None:
    """Get ChancellorOrchestrator instance (lazy import)."""
    global _orchestrator
    if _orchestrator is None:
        from AFO.api.chancellor_v2.orchestrator import ChancellorOrchestrator

        _orchestrator = ChancellorOrchestrator()
    return _orchestrator


# Feature flag for Orchestrator mode (default: True for new behavior)
USE_ORCHESTRATOR = os.getenv("AFO_USE_ORCHESTRATOR", "true").lower() == "true"

# Feature flag for parallel thinking+context7 (default: True for optimization)
USE_PARALLEL_PREPROCESS = os.getenv("AFO_PARALLEL_PREPROCESS", "true").lower() == "true"

"""Chancellor Graph V2 Runner (Contract Enforced).

Orchestrates node execution with checkpoint/event logging.
Contract: Sequential Thinking + Context7 are REQUIRED (no bypass).
"""


NodeFn = Callable[[GraphState], Awaitable[GraphState]]


async def _apply_thinking_and_context_parallel(state: GraphState, step: str) -> GraphState:
    """Apply Sequential Thinking and Context7 injection in parallel.

    OPTIMIZATION: Runs both operations concurrently since they are independent.
    Each operation writes to different keys in state.outputs:
    - Sequential Thinking -> state.outputs["sequential_thinking"][step]
    - Context7 -> state.outputs["context7"][step]
    """
    from AFO.api.chancellor_v2.thinking import _get_fallback_result

    # Build thought for this step (copied from apply_sequential_thinking)
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

    # Run both in parallel
    thinking_task = _call_sequential_thinking_async(
        thought=thought, thought_number=1, total_thoughts=1, next_thought_needed=False
    )
    context_task = inject_context_async(state, step)

    results = await asyncio.gather(thinking_task, context_task, return_exceptions=True)

    # Process thinking result
    thinking_result = results[0]
    if isinstance(thinking_result, Exception):
        logging.getLogger(__name__).warning(f"Parallel thinking failed: {thinking_result}")
        thinking_result = _get_fallback_result(thought, 1, 1, "parallel_error")

    # Store thinking result in state
    if "sequential_thinking" not in state.outputs:
        state.outputs["sequential_thinking"] = {}
    state.outputs["sequential_thinking"][step] = thinking_result

    # Process context result (it updates state directly, but we need to handle exceptions)
    context_result = results[1]
    if isinstance(context_result, Exception):
        logging.getLogger(__name__).warning(f"Parallel context7 failed: {context_result}")
        # Fallback: inject sync version
        state = inject_context(state, step)
    else:
        # context_result is GraphState with updated outputs - merge context7 data
        if hasattr(context_result, "outputs") and "context7" in context_result.outputs:
            if "context7" not in state.outputs:
                state.outputs["context7"] = {}
            state.outputs["context7"].update(context_result.outputs["context7"])

    logging.getLogger(__name__).info(f"[V2] Parallel preprocessing complete for {step}")
    return state


# SSOT: Chancellor Graph V2 Execution Order (5기둥 Trinity 완전 평가)
# This is the SINGLE SOURCE OF TRUTH for Chancellor Graph node execution sequence
# Assessment Cluster (TRUTH to ETERNITY) will be executed in parallel
ORDER = [
    "CMD",
    "PARSE",
    "ASSESSMENT_CLUSTER",  # Pseudo-step for parallel Trinity assessment
    "REFLECT",  # Deep Reflection Audit (PH30)
    "MIPRO",
    "MERGE",
    "EXECUTE",
    "VERIFY",
    "REPORT",
]

TRINITY_PILLARS = ["TRUTH", "GOODNESS", "BEAUTY", "SERENITY", "ETERNITY"]


def _now() -> float:
    """Get current Unix timestamp."""
    return time.time()


def _emit(
    state: GraphState,
    step: str,
    event: str,
    ok: bool,
    detail: dict[str, Any] | None = None,
) -> None:
    """Emit event to trace log."""
    payload: dict[str, Any] = {
        "ts": _now(),
        "trace_id": state.trace_id,
        "step": step,
        "event": event,
        "ok": ok,
    }
    if detail is not None:
        payload["detail"] = detail
    append_event(state.trace_id, payload)


def _checkpoint(state: GraphState, step: str) -> None:
    """Save checkpoint for current state."""
    payload = {
        "trace_id": state.trace_id,
        "request_id": state.request_id,
        "step": step,
        "input": state.input,
        "plan": state.plan,
        "outputs": state.outputs,
        "errors": state.errors,
        "started_at": state.started_at,
        "updated_at": state.updated_at,
    }
    save_checkpoint(state.trace_id, step, payload)


async def run_v2(input_payload: dict[str, Any], nodes: dict[str, NodeFn]) -> GraphState:
    """Execute graph with provided nodes.

    Contract: Sequential Thinking + Context7 are ALWAYS applied.
    No enable_* flags - this is enforced by design.

    Args:
        input_payload: Input from commander
        nodes: Dict mapping step names to node functions

    Returns:
        Final GraphState after execution
    """
    # Import thinking/context modules (Contract: these MUST be available)

    trace_id = uuid.uuid4().hex
    state = GraphState(
        trace_id=trace_id,
        request_id=uuid.uuid4().hex,
        input=input_payload,
        started_at=_now(),
        updated_at=_now(),
    )

    # Contract: Always inject Kingdom DNA at trace start (Constitutional SSOT)
    _emit(state, "INIT", "kingdom_dna_start", True)
    state = inject_kingdom_dna(state)
    _emit(state, "INIT", "kingdom_dna_complete", True)

    # Track contract enforcement status
    state.outputs["_meta"] = {
        "thinking_enforced": True,
        "context7_enforced": True,
        "kingdom_dna_injected": True,
        "parallel_assessment": True,
    }

    for step in ORDER:
        state.step = step

        if step == "ASSESSMENT_CLUSTER":
            # Parallel execution of 眞善美孝永
            _emit(state, step, "enter_cluster", True)

            if USE_ORCHESTRATOR:
                # OPTIMIZATION: Run ALL 5 pillars in true parallel
                # Previously: orchestrator awaited first, then SERENITY/ETERNITY sequentially
                # Now: Single asyncio.gather for all pillars at once
                orchestrator = _get_orchestrator()

                # Prepare SERENITY/ETERNITY tasks first (they start immediately)
                serenity_eternity_tasks = []
                for pillar in ["SERENITY", "ETERNITY"]:
                    fn = nodes.get(pillar)
                    if fn:
                        serenity_eternity_tasks.append(_execute_node_safe(state, pillar, fn))

                # Create orchestrator task (眞善美) - will run in parallel with 孝永
                orchestrator_task = orchestrator.orchestrate_assessment(state)

                # TRUE 5-PILLAR PARALLEL: All tasks start simultaneously
                all_results = await asyncio.gather(
                    orchestrator_task,  # Returns orchestrator results dict
                    *serenity_eternity_tasks,  # Returns GraphState objects
                    return_exceptions=True,
                )

                # Process orchestrator results (first item)
                orchestrator_results = all_results[0]
                if isinstance(orchestrator_results, Exception):
                    state.errors.append(f"Orchestrator failed: {orchestrator_results}")
                else:
                    state = orchestrator.aggregate_to_state(state, orchestrator_results)

                # Process SERENITY/ETERNITY results (remaining items)
                se_results = all_results[1:]
                for pillar_res in se_results:
                    if isinstance(pillar_res, GraphState):
                        for k, v in pillar_res.outputs.items():
                            if k in ["SERENITY", "ETERNITY"]:
                                state.outputs[k] = v
                        state.errors.extend(pillar_res.errors)
                    elif isinstance(pillar_res, Exception):
                        state.errors.append(f"Pillar execution failed: {pillar_res}")

                # Track orchestrator usage
                state.outputs.setdefault("_meta", {})["orchestrator_used"] = True
                state.outputs["_meta"]["true_5pillar_parallel"] = True

            else:
                # LEGACY: Original parallel execution for all 5 pillars
                tasks = []
                for pillar in TRINITY_PILLARS:
                    fn = nodes.get(pillar)
                    if fn:
                        tasks.append(_execute_node_safe(state, pillar, fn))

                pillar_results = await asyncio.gather(*tasks, return_exceptions=True)

                for pillar_res in pillar_results:
                    if isinstance(pillar_res, GraphState):
                        for k, v in pillar_res.outputs.items():
                            if k in TRINITY_PILLARS:
                                state.outputs[k] = v
                        state.errors.extend(pillar_res.errors)
                    elif isinstance(pillar_res, Exception):
                        state.errors.append(f"Pillar execution failed: {pillar_res}")

            state.updated_at = _now()
            _emit(state, step, "exit_cluster", True)
            _checkpoint(state, step)
            continue

        _emit(state, step, "enter", True)

        # Contract: Apply Sequential Thinking + Context7 BEFORE every node
        # OPTIMIZATION: Run in parallel when enabled (default: True)
        if USE_PARALLEL_PREPROCESS:
            state = await _apply_thinking_and_context_parallel(state, step)
        else:
            # Fallback: Sequential execution (legacy behavior)
            state = apply_sequential_thinking(state, step)
            state = inject_context(state, step)

        fn = nodes.get(step)
        if fn is None:
            state.errors.append(f"missing node: {step}")
            _emit(state, step, "missing_node", False)
            _checkpoint(state, step)
            return state

        try:
            state = await fn(state)
            state.updated_at = _now()
            _emit(state, step, "exit", True)
            _checkpoint(state, step)
        except Exception as e:
            state.errors.append(f"{step} failed: {type(e).__name__}: {e}")
            _emit(state, step, "error", False, {"error": f"{type(e).__name__}: {e}"})
            _checkpoint(state, step)
            return state

    # OPTIMIZATION: Save Evidence Pack in background (don't block response)
    # Fire-and-forget pattern for non-critical persistence
    asyncio.create_task(_save_evidence_pack(state))

    return state


def _write_evidence_file_sync(evidence_file: str, record_json: str) -> None:
    """Synchronous file write helper for asyncio.to_thread."""
    with open(evidence_file, "a", encoding="utf-8") as f:
        f.write(record_json + "\n")


async def _save_evidence_pack(state: GraphState) -> None:
    """Save the results of this run to the Council Evidence Pack (.jsonl) and Mem0.

    OPTIMIZATION: File I/O runs in thread pool, Mem0 save runs in parallel.
    """
    try:
        settings = get_settings()

        # Ensure artifacts directory exists
        evidence_dir = os.path.join(settings.ARTIFACTS_DIR, "council_runs")
        os.makedirs(evidence_dir, exist_ok=True)

        # Create run record
        record = {
            "timestamp": datetime.fromtimestamp(_now(), UTC).isoformat(),
            "trace_id": state.trace_id,
            "request_id": state.request_id,
            "command": state.input.get("command", ""),
            "outputs": state.outputs,
            "errors": state.errors,
            "decision": state.outputs.get("MERGE", {}),
        }

        # Append to daily evidence pack
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        evidence_file = os.path.join(evidence_dir, f"council_{date_str}.jsonl")
        record_json = json_dumps(record, ensure_ascii=False)

        # OPTIMIZATION: Parallel file write (in thread) + Mem0 save
        await asyncio.gather(
            asyncio.to_thread(_write_evidence_file_sync, evidence_file, record_json),
            _save_to_mem0(state, record),
            return_exceptions=True,  # Don't let one failure crash the other
        )

    except Exception as e:
        # Don't let evidence pack failure crash the command, but log it
        logging.getLogger(__name__).error(f"Failed to save Council Evidence Pack: {e}")


async def _save_to_mem0(state: GraphState, record: dict[str, Any]) -> None:
    """Save session memory to Mem0 for long-term persistence (TICKET-047)."""
    try:
        from memory.mem0_client import get_memory_client

        memory_client = get_memory_client()

        # Create memory content from the session
        decision = record.get("decision", {})
        trinity_score = decision.get("trinity_score", 0)
        decision_mode = decision.get("mode", "UNKNOWN")

        memory_content = (
            f"Chancellor Session {state.trace_id[:8]}: "
            f"Command '{record.get('command', 'unknown')[:50]}' -> "
            f"Decision: {decision_mode} (Trinity: {trinity_score:.1f})"
        )

        # Save to Mem0 with session metadata
        result = memory_client.add_memory(
            content=memory_content,
            user_id="chancellor_system",
            metadata={
                "trace_id": state.trace_id,
                "request_id": state.request_id,
                "decision_mode": decision_mode,
                "trinity_score": trinity_score,
                "pillar_scores": decision.get("pillar_scores", {}),
                "timestamp": record.get("timestamp", ""),
                "source": "chancellor_v2",
            },
            session_id=f"session_{state.trace_id[:8]}",
            run_id=state.request_id,
        )

        if result.get("success"):
            logging.getLogger(__name__).debug(
                f"Mem0 memory saved: {state.trace_id[:8]} ({result.get('latency_ms', 0):.1f}ms)"
            )

    except ImportError:
        # Mem0 not available, skip silently
        pass
    except Exception as e:
        # Don't let Mem0 failure crash the command
        logging.getLogger(__name__).warning(f"Mem0 save failed (non-critical): {e}")


async def _execute_node_safe(state: GraphState, step: str, fn: NodeFn) -> GraphState:
    """Helper to execute a node safely for parallel cluster."""

    # Create a shallow copy of state for this parallel branch to avoid race conditions on dicts
    # OPTIMIZATION: Use shallow copy instead of deepcopy - each parallel branch only adds
    # its own pillar key (SERENITY, ETERNITY, etc.) and doesn't modify existing values
    local_state = GraphState(
        trace_id=state.trace_id,
        request_id=state.request_id,
        input=state.input,
        plan=state.plan,
        outputs={**state.outputs},  # Shallow copy: O(n) keys vs O(n*m) deepcopy
        errors=[],  # Start with clean errors for this branch
        step=step,
        started_at=state.started_at,
        updated_at=state.updated_at,
    )

    # OPTIMIZATION: Use parallel preprocessing when enabled
    if USE_PARALLEL_PREPROCESS:
        local_state = await _apply_thinking_and_context_parallel(local_state, step)
    else:
        local_state = apply_sequential_thinking(local_state, step)
        local_state = inject_context(local_state, step)

    try:
        return await fn(local_state)
    except Exception as e:
        local_state.errors.append(f"{step} failed: {e}")
        return local_state
