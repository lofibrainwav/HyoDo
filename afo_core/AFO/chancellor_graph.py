from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any

from AFO.agents.heo_jun_core import heo_jun
from AFO.agents.jeong_yak_yong_core import jeong_yak_yong
from AFO.agents.kim_yu_sin_core import kim_yu_sin
from AFO.agents.ryu_seong_ryong_core import ryu_seong_ryong

logger = logging.getLogger(__name__)

from AFO.api.chancellor_v2.graph import nodes
from AFO.api.chancellor_v2.graph.runner import run_v2 as run_chancellor_v2
from AFO.chancellor_mipro_plugin import ChancellorMiproPlugin
from AFO.config.settings import get_settings
from AFO.mipro import Example, Module, mipro_optimizer

# Import checkpointer utilities
from AFO.persistence.langgraph_checkpointer import get_checkpointer as get_postgres_checkpointer
from AFO.utils.redis_saver import AsyncRedisSaver

"""Chancellor Graph V2 - AFO Kingdom Integration Layer.

Provides unified interface for Chancellor Graph V2 operations.
SSOT Contract: Sequential Thinking + Context7 are REQUIRED.

Performance Optimizations:
- Default nodes caching to avoid recreation overhead
- Lazy initialization of checkpointers
- Efficient state serialization
"""


# Import Chancellor Graph V2 components

# Performance optimization: Cache for default nodes to avoid recreation
_DEFAULT_NODES_CACHE = None


def _get_default_nodes() -> dict[str, Any]:
    """Get cached default nodes to avoid recreation overhead."""
    global _DEFAULT_NODES_CACHE
    if _DEFAULT_NODES_CACHE is None:
        _DEFAULT_NODES_CACHE = {
            "CMD": nodes.cmd_node,
            "PARSE": nodes.parse_node,
            "TRUTH": nodes.truth_node,
            "GOODNESS": nodes.goodness_node,
            "BEAUTY": nodes.beauty_node,
            "REFLECT": nodes.reflect_node,
            "SERENITY": nodes.serenity_node,
            "ETERNITY": nodes.eternity_node,
            "MERGE": nodes.merge_node,
            "EXECUTE": nodes.execute_node,
            "VERIFY": nodes.verify_node,
            "REPORT": nodes.report_node,
            "SOCRATES": nodes.socrates_node,
            "DELEGATE": None,  # Will be overridden in run_v2
        }
    return _DEFAULT_NODES_CACHE


# Create unified chancellor_graph interface
class ChancellorGraph:
    """Unified Chancellor Graph interface."""

    @staticmethod
    async def run_v2(
        input_payload: dict, nodes_dict: dict | None = None, thread_id: str | None = None
    ) -> dict:
        """Run Chancellor Graph V2 with default nodes if not provided.

        Args:
            input_payload: Input payload for graph execution
            nodes_dict: Optional custom nodes dict
            thread_id: Optional thread ID for state persistence

        Returns:
            Execution result as dict
        """
        # Default node configuration (performance optimized with caching)
        default_nodes = _get_default_nodes()

        # Merge with provided nodes_dict, overriding defaults where provided
        if nodes_dict is None:
            nodes_dict = default_nodes.copy()
        else:
            nodes_dict = {**default_nodes, **{k: v for k, v in nodes_dict.items() if v is not None}}

        # Always add MIPRO node (NO-OP by default, feature-flag controlled)
        async def mipro_node(state):
            """MIPRO optimization node for Chancellor Graph (NO-OP by default)."""
            try:
                plugin = ChancellorMiproPlugin()
                plan = plugin.plan()

                if not plan.enabled:
                    # NO-OP: feature flags not enabled, do nothing
                    return state

                # Feature flags enabled: perform actual MIPRO optimization
                try:
                    # Prepare mock program and examples for MIPROv2
                    # In real implementation, this would come from graph inputs
                    mock_program = Module()
                    mock_trainset = [
                        Example(input="test input", output="test output"),
                        Example(input="another input", output="another output"),
                    ]

                    # Run MIPROv2 optimization
                    # NOTE: If MIPRO compilation is slow/async, it should be awaited.
                    # For now, keeping it sync as per original implementation but wrapped in async node.
                    optimized_program = mipro_optimizer.compile(
                        student=mock_program, trainset=mock_trainset
                    )

                    # SSOT: MIPRO output size limit - keep summary only to prevent Graph state pollution
                    # Raw traces/candidates go to artifacts, not state.outputs
                    state.outputs["_mipro"] = {
                        "status": "optimized",
                        "score": getattr(optimized_program, "_mipro_score", 0.8),
                        "trials": getattr(optimized_program, "_mipro_trials", 0),
                        "config": getattr(optimized_program, "_mipro_config", {}),
                        "optimized": getattr(optimized_program, "_mipro_optimized", False),
                    }

                except ImportError as e:
                    # MIPRO modules not available
                    state.outputs["_mipro"] = {
                        "status": "modules_missing",
                        "error": str(e),
                    }
                except Exception as e:
                    # MIPRO execution failed
                    state.outputs["_mipro"] = {"status": "failed", "error": str(e)}

            except Exception:
                # Plugin system failed, fallback to NO-OP
                pass

            return state

        async def delegate_node(state):
            """Parallel Delegation Node. Invokes sub-scholars in parallel."""
            try:
                from AFO.infrastructure.llm.scholar_utils import scholar_collaboration
                from AFO.serenity.context_guard import context_guard

                command = state.input.get("command", "")
                # Extract evidence to keep context lean (Phase 50)
                evidence = context_guard.extract_evidence(command, focus_topic="goal analysis")

                # Determine which scholars to involve based on evidence
                recommendation = scholar_collaboration.get_collaboration_recommendation(
                    primary_scholar="류성룡 (Ryu Seong-ryong)",
                    task_complexity="complex",
                    trinity_score=state.outputs.get("TRUTH", {}).get("score", 90.0),
                )

                scholars = [recommendation["primary"]] + recommendation["collaborators"]
                logger.info(f"[V2.1] Delegating to scholars in parallel: {scholars}")

                # Load hierarchical context for the command (Phase 50)
                hierarchical_context = context_guard.load_hierarchical_context(os.getcwd())
                full_command = f"{hierarchical_context}\n\nCommand: {command}"

                # Create background tasks for each scholar
                tasks = []
                for s in scholars:
                    if "허준" in s:
                        tasks.append(asyncio.create_task(heo_jun.run(full_command)))
                    elif "정약용" in s:
                        tasks.append(asyncio.create_task(jeong_yak_yong.run(full_command)))
                    elif "류성룡" in s:
                        tasks.append(asyncio.create_task(ryu_seong_ryong.run(full_command)))
                    elif "김유신" in s:
                        tasks.append(asyncio.create_task(kim_yu_sin.run(full_command)))
                    else:
                        tasks.append(asyncio.create_task(asyncio.sleep(0.1)))

                results = await asyncio.gather(*tasks)
                state.outputs["DELEGATE"] = {
                    "status": "parallel_completed",
                    "scholars_involved": scholars,
                    "results": results,
                    "reasoning": recommendation["reasoning"],
                    "evidence_used": evidence,  # Pass evidence to 3 Strategists
                }
            except Exception as e:
                state.errors.append(f"Delegation failed: {e}")

            return state

        # Always register background delegation and MIPRO nodes
        nodes_dict["DELEGATE"] = delegate_node
        nodes_dict["MIPRO"] = mipro_node

        # TICKET-047 Phase 2: Initialize checkpointer for thread-based persistence
        checkpointer = None
        if thread_id:
            checkpointer = await ChancellorGraph._get_checkpointer(thread_id)

        # Load previous state if thread_id provided (reserved for future use)
        if checkpointer and thread_id:
            _ = await checkpointer.load_state(thread_id)

        try:
            state = await run_chancellor_v2(input_payload, nodes_dict)

            # Extract DecisionResult from MERGE node
            merge_output = state.outputs.get("MERGE", {})
            decision_dict = merge_output if isinstance(merge_output, dict) else {}

            # Convert GraphState to dict for compatibility
            result = {
                "trace_id": state.trace_id,
                "request_id": state.request_id,
                "input": state.input,
                "plan": state.plan,
                "outputs": state.outputs,
                "errors": state.errors,
                "step": state.step,
                "started_at": state.started_at,
                "updated_at": state.updated_at,
                "success": decision_dict.get("mode") == "AUTO_RUN",  # Use DecisionResult mode
                "error_count": len(state.errors),
                # Add DecisionResult fields for transparency
                "decision": decision_dict,
                # TICKET-047: Add thread information
                "thread_id": thread_id,
                "state_persisted": checkpointer is not None,
            }

            # Save state if checkpointer available
            if checkpointer and thread_id:
                await checkpointer.save_state(
                    thread_id,
                    {
                        "trace_id": state.trace_id,
                        "request_id": state.request_id,
                        "input": state.input,
                        "plan": state.plan,
                        "outputs": state.outputs,
                        "errors": state.errors,
                        "step": state.step,
                        "started_at": state.started_at,
                        "updated_at": state.updated_at,
                        "decision": decision_dict,
                    },
                )

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Chancellor Graph execution failed: {e}",
                "trace_id": None,
                "errors": [str(e)],
            }

    @staticmethod
    async def invoke(
        command: str, headers: dict[str, str] | None = None, thread_id: str | None = None, **kwargs
    ) -> dict:
        """Simple invoke method for backward compatibility.

        Args:
            command: Command string
            headers: Optional request headers for routing/shadow
            thread_id: Optional thread ID for state persistence
            **kwargs: Additional parameters

        Returns:
            Execution result
        """
        settings = get_settings()
        headers = headers or {}

        # Phase 24: Advanced Routing (Canary Override)
        # FastAPI headers in dict form are lowercase
        force_v2 = (
            headers.get("x-afo-engine", "").lower() == "v2"
            or headers.get("X-AFO-Engine", "").lower() == "v2"
        )
        v2_enabled = settings.CHANCELLOR_V2_ENABLED or force_v2
        shadow_enabled = settings.CHANCELLOR_V2_SHADOW_ENABLED and not v2_enabled

        # 1. Main Path
        try:
            if v2_enabled:
                # V2 execution
                input_payload = {"command": command, **kwargs}
                result = await ChancellorGraph.run_v2(input_payload, thread_id=thread_id)
                result["engine"] = "V2 (Graph)"
                return result
            else:
                # V1 Fallback
                result = {
                    "success": True,
                    "engine": "V1 (Legacy)",
                    "input": command,
                    "outputs": {"V1": "Executed via legacy V1 engine (Canary OFF)"},
                }

                # 2. Shadow Path (PH24)
                # Combined condition per SIM102: shadow enabled AND random sampling
                if shadow_enabled and random.random() <= settings.CHANCELLOR_V2_DIFF_SAMPLING_RATE:
                    asyncio.create_task(ChancellorGraph._run_shadow_diff(command, result, **kwargs))

                return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Chancellor Graph invocation failed: {e}",
                "engine": "V2 (Graph)" if v2_enabled else "V1 (Legacy)",
            }

    @staticmethod
    async def _run_shadow_diff(command: str, v1_result: dict, **kwargs):
        """Execute V2 in background and save diff evidence."""
        try:
            input_payload = {"command": command, **kwargs}
            v2_result = await ChancellorGraph.run_v2(input_payload)

            # Prepare diff Evidence
            diff_entry = {
                "timestamp": time.time(),
                "input": command,
                "v1_engine": v1_result.get("engine"),
                "v2_trace_id": v2_result.get("trace_id"),
                "v1_success": v1_result.get("success"),
                "v2_success": v2_result.get("success"),
                "v2_error_count": v2_result.get("error_count", 0),
            }

            # Save to artifacts for SSOT evidence
            project_root = Path(__file__).parent.parent.parent.parent
            diff_dir = project_root / "artifacts" / "chancellor_shadow_diff"
            os.makedirs(diff_dir, exist_ok=True)
            filename = f"diff_{v2_result.get('trace_id') or int(time.time())}.json"

            with open(os.path.join(diff_dir, filename), "w") as f:
                json.dump(diff_entry, f, indent=2)

        except Exception:
            # Silent fail for shadow mode to avoid affecting production
            pass

    @staticmethod
    async def _get_checkpointer(_thread_id: str) -> ChancellorCheckpointer | None:
        """Get appropriate checkpointer based on configuration and availability.

        Priority: Postgres > Redis > Memory
        """
        settings = get_settings()

        # Try Postgres first (most durable)
        try:
            if settings.get("CHANCELLOR_POSTGRES_CHECKPOINTER_ENABLED", True):
                postgres_cp = get_postgres_checkpointer()
                if not postgres_cp.is_available():
                    await postgres_cp.initialize()
                if postgres_cp.is_available():
                    return ChancellorCheckpointer(postgres_cp.saver, "postgres")
        except Exception:
            pass

        # Try Redis second
        try:
            if settings.get("CHANCELLOR_REDIS_CHECKPOINTER_ENABLED", True):
                redis_saver = AsyncRedisSaver()
                return ChancellorCheckpointer(redis_saver, "redis")
        except Exception:
            pass

        # Fallback to memory-based checkpointer
        return ChancellorCheckpointer(MemoryCheckpointer(), "memory")


class ChancellorCheckpointer:
    """Simple checkpointer wrapper for Chancellor Graph state persistence."""

    def __init__(self, backend: Any, backend_type: str) -> None:
        self.backend = backend
        self.backend_type = backend_type

    async def load_state(self, thread_id: str) -> dict | None:
        """Load previous state for thread."""
        try:
            if self.backend_type == "postgres":
                # Postgres LangGraph saver
                from langchain_core.runnables import RunnableConfig

                config = RunnableConfig(configurable={"thread_id": thread_id})
                tuple_result = await self.backend.aget_tuple(config)
                if tuple_result:
                    return {
                        "checkpoint": tuple_result.checkpoint,
                        "metadata": tuple_result.metadata,
                        "config": tuple_result.config,
                    }
            elif self.backend_type == "redis":
                # Redis saver
                from langchain_core.runnables import RunnableConfig

                config = RunnableConfig(configurable={"thread_id": thread_id})
                tuple_result = await self.backend.aget_tuple(config)
                if tuple_result:
                    return {
                        "checkpoint": tuple_result.checkpoint,
                        "metadata": tuple_result.metadata,
                        "config": tuple_result.config,
                    }
            elif self.backend_type == "memory":
                # Memory checkpointer
                return await self.backend.load_state(thread_id)
        except Exception:
            pass
        return None

    async def save_state(self, thread_id: str, state: dict) -> None:
        """Save current state for thread."""
        try:
            if self.backend_type == "postgres":
                # Postgres LangGraph saver
                from langchain_core.runnables import RunnableConfig
                from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

                config = RunnableConfig(configurable={"thread_id": thread_id})
                checkpoint = Checkpoint(
                    v=1,
                    id=str(uuid.uuid4()),
                    ts=time.time(),
                    channel_values=state,
                    channel_versions={},
                    versions_seen={},
                    pending_sends=[],
                )
                metadata = CheckpointMetadata(
                    source="chancellor_graph", step=state.get("step", -1), writes=None
                )

                await self.backend.aput(config, checkpoint, metadata, {})

            elif self.backend_type == "redis":
                # Redis saver
                from langchain_core.runnables import RunnableConfig
                from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

                config = RunnableConfig(configurable={"thread_id": thread_id})
                checkpoint = Checkpoint(
                    v=1,
                    id=str(uuid.uuid4()),
                    ts=time.time(),
                    channel_values=state,
                    channel_versions={},
                    versions_seen={},
                    pending_sends=[],
                )
                metadata = CheckpointMetadata(
                    source="chancellor_graph", step=state.get("step", -1), writes=None
                )

                await self.backend.aput(config, checkpoint, metadata, {})

            elif self.backend_type == "memory":
                # Memory checkpointer
                await self.backend.save_state(thread_id, state)
        except Exception:
            # Silent fail for checkpointer to avoid affecting main execution
            pass


class MemoryCheckpointer:
    """Simple in-memory checkpointer for development/testing."""

    def __init__(self) -> None:
        self._storage: dict[str, dict] = {}

    async def load_state(self, thread_id: str) -> dict | None:
        """Load state from memory."""
        return self._storage.get(thread_id)

    async def save_state(self, thread_id: str, state: dict) -> None:
        """Save state to memory."""
        self._storage[thread_id] = state.copy()


# Create singleton instance for backward compatibility
chancellor_graph = ChancellorGraph()


# Module-level mipro_node for external imports
async def mipro_node(state: Any) -> Any:
    """MIPRO optimization node for Chancellor Graph (NO-OP by default).

    This function is exported at module level for external imports.
    Actual optimization is feature-flag controlled via ChancellorMiproPlugin.
    """
    try:
        plugin = ChancellorMiproPlugin()
        plan = plugin.plan()

        if not plan.enabled:
            # NO-OP: feature flags not enabled, do nothing
            return state

        # Feature flags enabled: perform actual MIPRO optimization
        try:
            mock_program = Module()
            mock_trainset = [
                Example(input="test input", output="test output"),
                Example(input="another input", output="another output"),
            ]

            optimized_program = mipro_optimizer.compile(
                student=mock_program, trainset=mock_trainset
            )

            state.outputs["_mipro"] = {
                "status": "optimized",
                "score": getattr(optimized_program, "_mipro_score", 0.8),
                "trials": getattr(optimized_program, "_mipro_trials", 0),
                "config": getattr(optimized_program, "_mipro_config", {}),
                "optimized": getattr(optimized_program, "_mipro_optimized", False),
            }

        except ImportError as e:
            state.outputs["_mipro"] = {"status": "modules_missing", "error": str(e)}
        except Exception as e:
            state.outputs["_mipro"] = {"status": "failed", "error": str(e)}

    except Exception:
        # Plugin system failed, fallback to NO-OP
        pass

    return state


# Alias for backward compatibility
def build_chancellor_graph() -> ChancellorGraph:
    """Build and return a new ChancellorGraph instance."""
    return ChancellorGraph()
