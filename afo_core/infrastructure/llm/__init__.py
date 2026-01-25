# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Infrastructure LLM Package (infrastructure/llm/__init__.py)

Core infrastructure for LLM routing and execution.
"""

from .mcp_integration import (
    MCPIntegration,
    enrich_query_context,
    get_mcp_status,
    mcp_integration,
)

# Core config SSOT
from .model_config import (
    TASK_PATTERNS,
    ModelConfig,
    TaskType,
    get_compiled_patterns,
)

# Routing functions
from .model_routing import (
    DEFAULT_ESCALATION_THRESHOLD,
    ESCALATION_THRESHOLD,  # Backward compatibility alias
    TASK_THRESHOLD_MAP,
    classify_task,
    get_advanced_routing_info,
    get_escalation_model,
    get_escalation_threshold,
    get_model_for_task,
    get_model_with_escalation,
    get_routing_info,
    get_vision_model,
    should_escalate,
)
from .models import LLMConfig, LLMProvider, QualityTier, RoutingDecision
from .providers import call_llm, call_ollama, query_google

# Scholar utilities (extracted from model_routing.py)
from .scholar_utils import (
    AutoOptimizationEngine,
    ScholarCollaboration,
    ScholarMetrics,
    auto_optimizer,
    scholar_collaboration,
    scholar_metrics,
)
from .ssot_compliant_router import SSOTCompliantLLMRouter as LLMRouter

__all__ = [
    "LLMConfig",
    "LLMProvider",
    "QualityTier",
    "RoutingDecision",
    "call_llm",
    "call_ollama",
    "query_google",
    "LLMRouter",
    # Model Config SSOT
    "TaskType",
    "ModelConfig",
    "TASK_PATTERNS",
    "get_compiled_patterns",
    # Model Routing
    "classify_task",
    "get_model_for_task",
    "get_routing_info",
    # Escalation Pattern (Bottom-Up)
    "ESCALATION_THRESHOLD",  # Backward compatibility alias
    "DEFAULT_ESCALATION_THRESHOLD",
    "TASK_THRESHOLD_MAP",
    "get_escalation_threshold",
    "should_escalate",
    "get_escalation_model",
    "get_model_with_escalation",
    "get_vision_model",
    "get_advanced_routing_info",
    # MCP Integration
    "MCPIntegration",
    "mcp_integration",
    "enrich_query_context",
    "get_mcp_status",
    # Scholar Utilities
    "ScholarCollaboration",
    "ScholarMetrics",
    "AutoOptimizationEngine",
    "scholar_collaboration",
    "scholar_metrics",
    "auto_optimizer",
]
