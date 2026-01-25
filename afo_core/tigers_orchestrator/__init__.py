"""
왕국 5호장군(五虎將軍) 오케스트레이터

이 모듈은 2026년 1월 22일 기준 최신 리서치를 바탕으로
혁명적으로 설계된 5호장군 협업 메커니즘을 구현합니다.

구현된 혁명적 기술:
- LangGraph State Machine (Node Orchestration + Conditional Edges)
- Event-Driven Architecture (Pub/Sub + Message Bus)
- Circuit Breaker Pattern (Per-General Protection)
- Trinity Score Aggregation (Weighted Scoring + Dynamic Risk)
- Ambassador Pattern (Decision Execution)
- Protocol Buffers + Pydantic (Type-safe Contracts)
"""

from .circuit_breakers import (
    CircuitState,
    TigerCircuitBreaker,
)
from .decision_engine import (
    TigerGeneralsAmbassador,
)
from .event_bus import (
    TigerGeneralsEventBus,
)
from .message_protocol import (
    CrossPillarMessage,
    MessagePriority,
    MessageType,
)
from .models import (
    ActionType,
    BeautyCraftInput,
    BeautyCraftOutput,
    DecisionAction,
    DecisionType,
    EternityLogInput,
    EternityLogOutput,
    GoodnessGateInput,
    GoodnessGateOutput,
    SerenityDeployInput,
    SerenityDeployOutput,
    TigerCommandBase,
    TigerResponseBase,
    TruthGuardInput,
    TruthGuardOutput,
)
from .scoring import (
    TIGER_WEIGHTS,
    TrinityScoreAggregator,
)
from .state_machine import (
    ExecutionStrategy,
    TigerGeneralsState,
    run_tiger_generals_orchestration,
)

__all__ = [
    # Models
    "TigerCommandBase",
    "TigerResponseBase",
    "TruthGuardInput",
    "TruthGuardOutput",
    "GoodnessGateInput",
    "GoodnessGateOutput",
    "BeautyCraftInput",
    "BeautyCraftOutput",
    "SerenityDeployInput",
    "SerenityDeployOutput",
    "EternityLogInput",
    "EternityLogOutput",
    "DecisionAction",
    "DecisionType",
    "ActionType",
    # Event Bus
    "TigerGeneralsEventBus",
    # Message Protocol
    "CrossPillarMessage",
    "MessageType",
    "MessagePriority",
    # State Machine
    "TigerGeneralsState",
    "ExecutionStrategy",
    "run_tiger_generals_orchestration",
    # Scoring
    "TrinityScoreAggregator",
    "TIGER_WEIGHTS",
    # Decision Engine
    "TigerGeneralsAmbassador",
    # Circuit Breakers
    "TigerCircuitBreaker",
    "CircuitState",
]
