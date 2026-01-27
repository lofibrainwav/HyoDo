# Trinity Score: 90.0 (Established by Chancellor)
"""Multi-Agent Router for AFO Kingdom (Council of Minds)
다중 에이전트 오케스트레이션 API.

Orchestrates the Council of Minds (Jang Yeong-sil, Yi Sun-sin, Shin Saimdang) using LangGraph.
Implements specific nodes for Truth, Goodness, and Beauty, and a Consensus node for final decision.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any, TypedDict
from uuid import uuid4

from fastapi import APIRouter
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from AFO.llm_router import llm_router
from AFO.utils.standard_shield import shield
from config.settings import settings

logger = logging.getLogger("AFO.MultiAgent")
router = APIRouter(prefix="/api/multi-agent", tags=["Multi-Agent Orchestration"])


# --- Pydantic Models for API ---


class TaskRequest(BaseModel):
    """Request for multi-agent task execution."""

    task: str
    context: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60


class OrchestrationResult(BaseModel):
    """Result of multi-agent orchestration."""

    task_id: str
    status: str
    final_response: str
    consensus_reached: bool
    trinity_score: float
    agent_responses: dict[str, Any]
    total_execution_time_ms: int
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# --- Council Graph State ---


class CouncilState(TypedDict):
    """State for the Council of Minds graph."""

    task_id: str
    task: str
    context: dict[str, Any]

    # 3-Pillar Outputs
    truth_output: dict[str, Any] | None
    goodness_output: dict[str, Any] | None
    beauty_output: dict[str, Any] | None

    # Final Consensus
    consensus_output: dict[str, Any] | None
    trinity_score: float
    final_decision: str

    errors: list[str]
    start_time: float


# --- Council Nodes ---


async def truth_node(state: CouncilState) -> dict[str, Any]:
    """Jang Yeong-sil (眞) Node: Technical Truth & Architecture."""
    logger.info(f"🦾 [TruthNode] Analyzing: {state['task'][:50]}...")
    prompt = f"""
    You are Jang Yeong-sil (眞), the Technical Strategist.
    Analyze the following task for technical feasibility, architectural soundness, and truth.

    Task: {state["task"]}
    Context: {state["context"]}

    Output JSON: {{ "score": float, "analysis": str, "technical_risks": list[str] }}
    """
    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt, scholar_key="truth_scholar", context={"role": "technical_architect"}
            ),
            timeout=settings.AFO_PILLAR_TIMEOUT,
        )
        # Parse JSON from response
        text = response.get("response", "{}").strip().replace("```json", "").replace("```", "")
        output = json.loads(text)
        return {"truth_output": output}
    except Exception as e:
        logger.error(f"[TruthNode] Failed: {e}")
        return {"truth_output": {"score": 0.5, "analysis": "Analysis failed", "error": str(e)}}


async def goodness_node(state: CouncilState) -> dict[str, Any]:
    """Yi Sun-sin (善) Node: Ethics, Risk, & Stability."""
    logger.info(f"🛡️ [GoodnessNode] Assessing risk: {state['task'][:50]}...")
    prompt = f"""
    You are Yi Sun-sin (善), the Guardian Strategist.
    Analyze the following task for ethical safety, security risks, and stability.

    Task: {state["task"]}

    Output JSON: {{ "score": float, "analysis": str, "safety_concerns": list[str] }}
    """
    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt, scholar_key="goodness_scholar", context={"role": "risk_manager"}
            ),
            timeout=settings.AFO_PILLAR_TIMEOUT,
        )
        text = response.get("response", "{}").strip().replace("```json", "").replace("```", "")
        output = json.loads(text)
        return {"goodness_output": output}
    except Exception as e:
        logger.error(f"[GoodnessNode] Failed: {e}")
        return {"goodness_output": {"score": 0.5, "analysis": "Analysis failed", "error": str(e)}}


async def beauty_node(state: CouncilState) -> dict[str, Any]:
    """Shin Saimdang (美) Node: UX, Narrative, & Aesthetics."""
    logger.info(f"🎭 [BeautyNode] Designing: {state['task'][:50]}...")
    prompt = f"""
    You are Shin Saimdang (美), the Art Strategist.
    Analyze the following task for user experience, narrative flow, and beauty.

    Task: {state["task"]}

    Output JSON: {{ "score": float, "analysis": str, "ux_suggestions": list[str] }}
    """
    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt, scholar_key="beauty_scholar", context={"role": "ux_designer"}
            ),
            timeout=settings.AFO_PILLAR_TIMEOUT,
        )
        text = response.get("response", "{}").strip().replace("```json", "").replace("```", "")
        output = json.loads(text)
        return {"beauty_output": output}
    except Exception as e:
        logger.error(f"[BeautyNode] Failed: {e}")
        return {"beauty_output": {"score": 0.5, "analysis": "Analysis failed", "error": str(e)}}


async def consensus_node(state: CouncilState) -> dict[str, Any]:
    """Chancellor Consensus Node: Weighted Scoring & Final Decision."""
    logger.info("⚖️ [ConsensusNode] Weighing opinions...")

    t_out = state.get("truth_output", {})
    g_out = state.get("goodness_output", {})
    b_out = state.get("beauty_output", {})

    t_score = t_out.get("score", 0.0)
    g_score = g_out.get("score", 0.0)
    b_score = b_out.get("score", 0.0)

    # Trinity Score Formula: 0.35*T + 0.35*G + 0.20*B + 0.1(Default for S/E)
    trinity_score = (t_score * 35) + (g_score * 35) + (b_score * 20) + 10.0

    consensus_reached = trinity_score >= 70.0  # Threshold

    final_summary = f"""
    🤝 Council Consensus Reached: {consensus_reached} (Score: {trinity_score:.1f})

    🦾 Truth (Jang Yeong-sil): {t_out.get("analysis")}
    🛡️ Goodness (Yi Sun-sin): {g_out.get("analysis")}
    🎭 Beauty (Shin Saimdang): {b_out.get("analysis")}
    """

    return {
        "final_decision": final_summary,
        "trinity_score": trinity_score,
        "consensus_output": {"reached": consensus_reached, "details": final_summary},
    }


# --- Graph Construction ---


def build_council_graph() -> Any:
    workflow = StateGraph(CouncilState)

    workflow.add_node("truth", truth_node)
    workflow.add_node("goodness", goodness_node)
    workflow.add_node("beauty", beauty_node)
    workflow.add_node("consensus", consensus_node)

    # Parallel Execution of Pillars
    workflow.set_entry_point("truth")
    workflow.set_entry_point("goodness")
    workflow.set_entry_point("beauty")

    # All lead to Consensus
    workflow.add_edge("truth", "consensus")
    workflow.add_edge("goodness", "consensus")
    workflow.add_edge("beauty", "consensus")

    workflow.add_edge("consensus", END)

    return workflow.compile()


# Singleton Graph
council_graph = build_council_graph()


# --- API Endpoints ---


@shield(pillar="善")
@router.post("/execute", response_model=OrchestrationResult)
async def execute_council_task(request: TaskRequest) -> OrchestrationResult:
    """Execute a task via the Council of Minds."""
    task_id = str(uuid4())[:8]
    start_time = datetime.now(UTC)

    initial_state = CouncilState(
        task_id=task_id,
        task=request.task,
        context=request.context,
        truth_output={},
        goodness_output={},
        beauty_output={},
        consensus_output={},
        trinity_score=0.0,
        final_decision="",
        errors=[],
        start_time=start_time.timestamp(),
    )

    # Run Graph
    result_state = await council_graph.ainvoke(initial_state)

    duration = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

    return OrchestrationResult(
        task_id=task_id,
        status="completed",
        final_response=result_state["final_decision"],
        consensus_reached=result_state["consensus_output"].get("reached", False),
        trinity_score=result_state["trinity_score"],
        agent_responses={
            "truth": result_state["truth_output"],
            "goodness": result_state["goodness_output"],
            "beauty": result_state["beauty_output"],
        },
        total_execution_time_ms=duration,
    )


@shield(pillar="善")
@router.get("/health")
async def council_health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "system": "Council of Minds (LangGraph)",
        "agents": ["Jang Yeong-sil", "Yi Sun-sin", "Shin Saimdang"],
        "graph_state": "Compiled",
    }
