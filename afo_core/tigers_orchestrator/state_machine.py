"""
LangGraph State Machine for Tiger Generals (5호장군)

Implements LangGraph-style state machine for 5호장군 orchestration.
Each 5호장군 becomes a node with conditional edges.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, TypedDict

from .scoring import TIGER_WEIGHTS

if TYPE_CHECKING:
    from .event_bus import TigerGeneralsEventBus
    from .scoring import TrinityScoreAggregator

logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    ADAPTIVE = "adaptive"


class TigerGeneralsState(TypedDict, total=False):
    """5호장군 State Machine State"""

    # 입력
    input_data: dict[str, Any]
    context_id: str
    previous_decision: str | None
    current_timestamp: str
    execution_strategy: ExecutionStrategy | str

    # 5호장군 개별 State
    truth_guard_output: dict[str, Any] | None
    goodness_gate_output: dict[str, Any] | None
    beauty_craft_output: dict[str, Any] | None
    serenity_deploy_output: dict[str, Any] | None
    eternity_log_output: dict[str, Any] | None

    # 공유 State
    trinity_score: float
    risk_score: float
    decision: str | None

    # Circuit Breaker State
    circuit_state: dict[str, str]

    # 실행 추적
    execution_trace: list[dict[str, Any]]
    errors: list[str]

    # 완료 플래그
    all_generals_completed: bool


async def truth_guard_node(state: TigerGeneralsState) -> dict[str, Any]:
    """Node 1: 관우(眞) - 타입 검증"""
    logger.info("[Node: truth_guard] Starting type validation")

    try:
        from tigers.guan_yu import truth_guard

        result = truth_guard(state["input_data"])

        return {
            "truth_guard_output": result,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "truth_guard",
                    "result": result,
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }
    except Exception as e:
        logger.error(f"[Node: truth_guard] Error: {e}")
        state["errors"].append(f"truth_guard: {e!s}")
        return {
            "truth_guard_output": {"success": False, "error": str(e)},
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "truth_guard",
                    "error": str(e),
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }


async def goodness_gate_node(state: TigerGeneralsState) -> dict[str, Any]:
    """Node 2: 장비(善) - 위험 평가"""
    logger.info("[Node: goodnes_gate] Starting risk assessment")

    try:
        from tigers.zhang_fei import goodness_gate

        result = goodness_gate(
            risk_score=state.get("risk_score", 0.0),
            context={
                "truth_output": state.get("truth_guard_output"),
                "input_data": state.get("input_data"),
            },
        )

        risk_score = result if isinstance(result, float) else 0.0

        return {
            "goodness_gate_output": result,
            "risk_score": risk_score,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "goodness_gate",
                    "result": result,
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }
    except Exception as e:
        logger.error(f"[Node: goodnes_gate] Error: {e}")
        state["errors"].append(f"goodnes_gate: {e!s}")
        return {
            "goodness_gate_output": {"success": False, "error": str(e)},
            "risk_score": 50.0,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "goodness_gate",
                    "error": str(e),
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }


async def beauty_craft_node(state: TigerGeneralsState) -> dict[str, Any]:
    """Node 3: 조운(美) - 코드 우아화"""
    logger.info("[Node: beauty_craft] Starting code enhancement")

    try:
        from tigers.zhao_yun import beauty_craft

        # Risk Score에 따라 조운 실행 결정
        if state["risk_score"] > 30.0:
            logger.warning(f"[Node: beauty_craft] Skipped due to high risk: {state['risk_score']}")
            return {
                "beauty_craft_output": "SKIPPED_HIGH_RISK",
                "execution_trace": state["execution_trace"]
                + [
                    {
                        "general": "beauty_craft",
                        "result": "SKIPPED",
                        "timestamp": state.get("current_timestamp"),
                    }
                ],
            }

        ux_level = min(10, int(100 - state["risk_score"] / 10))

        result = beauty_craft(
            code_snippet=state.get("input_data", {}).get("code", ""), ux_level=ux_level
        )

        return {
            "beauty_craft_output": result,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "beauty_craft",
                    "result": result,
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }
    except Exception as e:
        logger.error(f"[Node: beauty_craft] Error: {e}")
        state["errors"].append(f"beauty_craft: {e!s}")
        return {
            "beauty_craft_output": {"success": False, "error": str(e)},
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "beauty_craft",
                    "error": str(e),
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }


async def serenity_deploy_node(state: TigerGeneralsState) -> dict[str, Any]:
    """Node 4: 마초(孝) - 배포"""
    logger.info("[Node: serenity_deploy] Starting deployment")

    try:
        from tigers.ma_chao import serenity_deploy

        result = serenity_deploy(
            {
                "truth_output": state.get("truth_guard_output"),
                "goodness_output": state.get("goodness_gate_output"),
                "beauty_output": state.get("beauty_craft_output"),
            }
        )

        return {
            "serenity_deploy_output": result,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "serenity_deploy",
                    "result": result,
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }
    except Exception as e:
        logger.error(f"[Node: serenity_deploy] Error: {e}")
        state["errors"].append(f"serenity_deploy: {e!s}")
        return {
            "serenity_deploy_output": {"success": False, "error": str(e)},
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "serenity_deploy",
                    "error": str(e),
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }


async def eternity_log_node(state: TigerGeneralsState) -> dict[str, Any]:
    """Node 5: 황충(永) - Evidence 기록"""
    logger.info("[Node: eternity_log] Logging evidence")

    try:
        from tigers.huang_zhong import eternity_log

        result = eternity_log(
            action="COMPLETED_EXECUTION",
            details={
                "decision": state["decision"],
                "trinity_score": state["trinity_score"],
                "risk_score": state["risk_score"],
                "execution_trace": state["execution_trace"],
            },
        )

        return {
            "eternity_log_output": result,
            "all_generals_completed": True,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "eternity_log",
                    "result": result,
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }
    except Exception as e:
        logger.error(f"[Node: eternity_log] Error: {e}")
        state["errors"].append(f"eternity_log: {e!s}")
        return {
            "eternity_log_output": {"success": False, "error": str(e)},
            "all_generals_completed": True,
            "execution_trace": state["execution_trace"]
            + [
                {
                    "general": "eternity_log",
                    "error": str(e),
                    "timestamp": state.get("current_timestamp"),
                }
            ],
        }


def should_execute_parallel(state: TigerGeneralsState) -> bool:
    """병렬 실행 여부 결정"""
    return state["execution_strategy"] == ExecutionStrategy.PARALLEL


def should_execute_sequential(state: TigerGeneralsState) -> bool:
    """순차 실행 여부 결정"""
    return state["execution_strategy"] == ExecutionStrategy.SEQUENTIAL


def should_execute_adaptive(state: TigerGeneralsState) -> bool:
    """적응 실행 여부 결정"""
    return state["execution_strategy"] == ExecutionStrategy.ADAPTIVE


def calculate_aggregated_scores(
    truth_output: dict[str, Any],
    goodness_output: dict[str, Any],
    beauty_output: dict[str, Any],
    serenity_output: dict[str, Any],
    eternity_output: dict[str, Any],
) -> dict[str, float]:
    """개별 점수 집계"""
    scores = {}

    # 관우 점수
    if isinstance(truth_output, dict) and "score" in truth_output:
        scores["truth_guard"] = truth_output["score"]
    elif isinstance(truth_output, dict) and "success" in truth_output:
        scores["truth_guard"] = 100.0
    else:
        scores["truth_guard"] = 0.0

    # 장비 점수
    if isinstance(goodness_output, dict) and "score" in goodness_output:
        scores["goodness_gate"] = goodness_output["score"]
    elif isinstance(goodness_output, dict) and "risk_score" in goodness_output:
        scores["goodness_gate"] = 100.0 - min(goodness_output.get("risk_score", 0.0) * 2, 100.0)
    else:
        scores["goodness_gate"] = 0.0

    # 조운 점수
    if isinstance(beauty_output, dict) and "beauty_score" in beauty_output:
        scores["beauty_craft"] = beauty_output.get("beauty_score", 0.0)
    else:
        scores["beauty_craft"] = 0.0

    # 마초 점수
    if isinstance(serenity_output, dict) and "score" in serenity_output:
        scores["serenity_deploy"] = serenity_output.get("score", 0.0)
    elif isinstance(serenity_output, dict) and "success" in serenity_output:
        scores["serenity_deploy"] = 100.0
    else:
        scores["serenity_deploy"] = 0.0

    # 황충 점수
    is_eternity_success = isinstance(eternity_output, dict) and (
        "success" in eternity_output or eternity_output.get("persisted")
    )
    if is_eternity_success:
        scores["eternity_log"] = 100.0
    else:
        scores["eternity_log"] = 0.0

    return scores


def get_decision(trinity_score: float, risk_score: float) -> str:
    """Decision Matrix"""
    if trinity_score >= 90.0 and risk_score <= 10.0:
        return "AUTO_RUN"
    elif 70.0 <= trinity_score < 90.0 and risk_score <= 10.0:
        return "ASK_COMMANDER"
    else:
        return "BLOCK"


async def run_tiger_generals_orchestration(
    event_bus: TigerGeneralsEventBus,
    input_data: dict[str, Any],
    context_id: str,
    scoring: TrinityScoreAggregator | None = None,
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL,
) -> TigerGeneralsState:
    """5호장군 오케스트레이션 메인 함수"""

    logger.info(f"[Orchestration] Starting 5호장군 orchestration with context: {context_id}")

    # 1. 초기 State 생성
    state = TigerGeneralsState(
        input_data=input_data, context_id=context_id, current_timestamp=datetime.now().isoformat()
    )

    # 2. Event Bus 초기화
    generals = ["truth_guard", "goodness_gate", "beauty_craft", "serenity_deploy", "eternity_log"]
    for general in generals:
        await event_bus.create_channel(general)
        logger.info(f"[Orchestration] Created channel for {general}")

    # 3. 개별 점수 집계
    aggregated_scores: dict[str, float] = {}

    # 4. 5호장군 병렬 실행
    if should_execute_parallel(state):
        logger.info("[Orchestration] Using PARALLEL execution strategy")

        results = await asyncio.gather(
            truth_guard_node(state),
            goodness_gate_node(state),
            beauty_craft_node(state),
            serenity_deploy_node(state),
            eternity_log_node(state),
        )
        truth, goodness, beauty, serenity, eternity = results
        state["truth_guard_output"] = truth.get("truth_guard_output")
        state["goodness_gate_output"] = goodness.get("goodness_gate_output")
        state["beauty_craft_output"] = beauty.get("beauty_craft_output")
        state["serenity_deploy_output"] = serenity.get("serenity_deploy_output")
        state["eternity_log_output"] = eternity.get("eternity_log_output")

        # Update trace and other fields explicitly if needed
        state["execution_trace"] = (
            (state.get("execution_trace") or [])
            + (truth.get("execution_trace") or [])
            + (goodness.get("execution_trace") or [])
            + (beauty.get("execution_trace") or [])
            + (serenity.get("execution_trace") or [])
            + (eternity.get("execution_trace") or [])
        )
    else:
        logger.info("[Orchestration] Using SEQUENTIAL execution strategy")
        # Sequential execution is handled by nodes directly updating state or returning dicts
        # For simplicity in this mock, we assume nodes are called in order
        truth_res = await truth_guard_node(state)
        state["truth_guard_output"] = truth_res.get("truth_guard_output")
        state["execution_trace"] = truth_res.get("execution_trace", [])

        goodness_res = await goodness_gate_node(state)
        state["goodness_gate_output"] = goodness_res.get("goodness_gate_output")
        state["risk_score"] = goodness_res.get("risk_score", 0.0)
        state["execution_trace"] = goodness_res.get("execution_trace", [])

        beauty_res = await beauty_craft_node(state)
        state["beauty_craft_output"] = beauty_res.get("beauty_craft_output")
        state["execution_trace"] = beauty_res.get("execution_trace", [])

    # 5. Risk Score 계산 (장비만)
    if state.get("goodness_gate_output") and isinstance(state["goodness_gate_output"], dict):
        state["risk_score"] = state["goodness_gate_output"].get("risk_score", 0.0)

    # 6. 마초 배포 + 황충 기록
    serenity_result = await serenity_deploy_node(state)
    state["serenity_deploy_output"] = serenity_result.get("serenity_deploy_output")
    state["execution_trace"] = serenity_result.get("execution_trace", [])

    eternity_result = await eternity_log_node(state)
    state["eternity_log_output"] = eternity_result.get("eternity_log_output")
    state["execution_trace"] = eternity_result.get("execution_trace", [])
    state["all_generals_completed"] = bool(eternity_result.get("all_generals_completed", False))

    # 7. Trinity Score 계산
    aggregated_scores = calculate_aggregated_scores(
        state.get("truth_guard_output") or {},
        state.get("goodness_gate_output") or {},
        state.get("beauty_craft_output") or {},
        state.get("serenity_deploy_output") or {},
        state.get("eternity_log_output") or {},
    )

    trinity_score = (
        sum(score * TIGER_WEIGHTS.get(name, 0.0) for name, score in aggregated_scores.items())
        if aggregated_scores
        else 0.0
    )

    state["trinity_score"] = trinity_score

    # 8. Decision Matrix 실행
    state["decision"] = get_decision(trinity_score, state["risk_score"])

    # 9. 완료 플래그 설정
    if state["all_generals_completed"]:
        logger.info("[Orchestration] 5호장군 orchestration completed successfully")
        logger.info(f"[Orchestration] Trinity Score: {state['trinity_score']:.2f}")
        logger.info(f"[Orchestration] Risk Score: {state['risk_score']:.2f}")
        logger.info(f"[Orchestration] Decision: {state['decision']}")

    return state
