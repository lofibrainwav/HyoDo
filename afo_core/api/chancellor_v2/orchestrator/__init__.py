"""Chancellor Graph V2/V3 Orchestrator Package.

Orchestrator 패턴으로 3 Strategists를 독립 컨텍스트에서 병렬 실행합니다.

Components:
- StrategistContext: 독립 실행 컨텍스트
- StrategistRegistry: 서브에이전트 등록/관리
- ResultAggregator: 결과 통합 및 Trinity Score 계산
- ChancellorOrchestrator: 단일 진입점 Orchestrator
- CircuitBreaker: 장애 격리 및 복구
- CrossPillarBus: Strategist 간 통신
- LearningBridge: 학습 엔진 연동
- RedisStrategistRegistry: Redis 기반 영속화

V3 Components (Phase 1):
- CostAwareRouter: 비용 인식 모델 라우터 (API 비용 40% 절감)
- KeyTriggerRouter: 키워드 트리거 Strategist 선택 (불필요 평가 30% 감소)

V3 Components (Phase 2):
- ChancellorHooks: 라이프사이클 훅 시스템
- SessionPersistence: Redis 기반 세션 영속화/복구

V3 Components (Phase 3):
- BackgroundStrategist: 비동기 백그라운드 태스크 실행
- PreemptiveCompactor: 컨텍스트 윈도우 압축
"""

# V3 라우터 (Phase 1)
# 새로운 확장 컴포넌트
# V3 Phase 2: Hooks & Session Persistence
# V3 Phase 3: Background Strategist & Compactor
from .background_strategist import (
    BackgroundStrategist,
    BackgroundTask,
    TaskState,
    get_background_strategist,
)
from .chancellor_hooks import (
    ChancellorHooks,
    HookEvent,
    HookRegistration,
    HookResult,
    get_chancellor_hooks,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    StrategistCircuitBreakerManager,
)
from .cost_aware_router import (
    CostAwareRouter,
    CostTier,
    ModelConfig,
    get_cost_aware_router,
)
from .cross_pillar import (
    CrossPillarBus,
    CrossPillarMessage,
    MessageType,
    Priority,
    get_cross_pillar_bus,
)
from .key_trigger_router import (
    KeyTriggerRouter,
    TriggerPattern,
    get_key_trigger_router,
)
from .learning_bridge import (
    LearningBridge,
    PatternInsight,
    StrategistDecisionRecord,
    get_learning_bridge,
)
from .preemptive_compactor import (
    CompressionLevel,
    CompressionResult,
    CompressionStrategy,
    ContextMetrics,
    MessageItem,
    PreemptiveCompactor,
    get_preemptive_compactor,
)
from .redis_registry import (
    RedisStrategistRegistry,
    StrategistMetadata,
    get_redis_registry,
)
from .session_persistence import (
    ContextSnapshot,
    SessionData,
    SessionPersistence,
    get_session_persistence,
)
from .strategist_context import StrategistContext
from .sub_agent_registry import StrategistRegistry

# 선택적 임포트 (기존 컴포넌트)
try:
    from .chancellor_orchestrator import (
        STRATEGIST_NAMES,
        ChancellorOrchestrator,
        get_orchestrator,
    )
    from .result_aggregator import ResultAggregator
except ImportError:
    ChancellorOrchestrator = None  # type: ignore
    ResultAggregator = None  # type: ignore
    STRATEGIST_NAMES = {}  # type: ignore
    get_orchestrator = None  # type: ignore

__all__ = [
    # Core
    "StrategistContext",
    "StrategistRegistry",
    "ResultAggregator",
    "ChancellorOrchestrator",
    "STRATEGIST_NAMES",
    "get_orchestrator",
    # V3 Routers (Phase 1)
    "CostAwareRouter",
    "CostTier",
    "ModelConfig",
    "get_cost_aware_router",
    "KeyTriggerRouter",
    "TriggerPattern",
    "get_key_trigger_router",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitOpenError",
    "StrategistCircuitBreakerManager",
    # Cross-Pillar Communication
    "CrossPillarBus",
    "CrossPillarMessage",
    "MessageType",
    "Priority",
    "get_cross_pillar_bus",
    # Learning Bridge
    "LearningBridge",
    "PatternInsight",
    "StrategistDecisionRecord",
    "get_learning_bridge",
    # Redis Registry
    "RedisStrategistRegistry",
    "StrategistMetadata",
    "get_redis_registry",
    # V3 Phase 2: Hooks
    "ChancellorHooks",
    "HookEvent",
    "HookRegistration",
    "HookResult",
    "get_chancellor_hooks",
    # V3 Phase 2: Session Persistence
    "SessionPersistence",
    "SessionData",
    "ContextSnapshot",
    "get_session_persistence",
    # V3 Phase 3: Background Strategist
    "BackgroundStrategist",
    "BackgroundTask",
    "TaskState",
    "get_background_strategist",
    # V3 Phase 3: Preemptive Compactor
    "PreemptiveCompactor",
    "ContextMetrics",
    "CompressionResult",
    "CompressionStrategy",
    "CompressionLevel",
    "MessageItem",
    "get_preemptive_compactor",
]
