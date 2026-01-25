from __future__ import annotations

from typing import TYPE_CHECKING, Any

from AFO.domain.metrics.trinity_ssot import (
    THRESHOLD_ASK_RISK,
    THRESHOLD_ASK_TRINITY,
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
)
from AFO.observability.verdict_event import Decision, VerdictEvent, VerdictFlags

# Trinity Score Thresholds: SSOT from trinity_ssot.py

if TYPE_CHECKING:
    from collections.abc import Mapping

    from AFO.observability.verdict_logger import VerdictLogger


class ChancellorNode:
    """Node 04: Verdict - 최종 판결을 내리는 Chancellor의 심판대

    Trinity Score 기반으로 최종 결정을 내리고,
    Verdict Event를 생성하여 로깅합니다.
    """

    def __init__(self, logger: VerdictLogger | None = None) -> None:
        self.logger = logger

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Trinity Score 기반 최종 판결 로직"""

        trace_id = state.get("trace_id", "unknown")
        trinity_score = state.get("trinity_score", 0.0)
        risk_score = state.get("risk_score", 0.0)

        # Trinity Score 기반 판결 로직 (SSOT: trinity_ssot.py)
        if trinity_score >= THRESHOLD_AUTO_RUN_SCORE and risk_score <= THRESHOLD_AUTO_RUN_RISK:
            decision = Decision.AUTO_RUN
            dry_run_default = False
            residual_doubt = False
            rule_id = "HIGH_TRUST_AUTO_RUN"
        elif trinity_score >= THRESHOLD_ASK_TRINITY and risk_score <= THRESHOLD_ASK_RISK:
            decision = Decision.ASK_COMMANDER
            dry_run_default = True
            residual_doubt = True
            rule_id = "MEDIUM_TRUST_ASK_COMMANDER"
        else:
            decision = Decision.BLOCK
            dry_run_default = True
            residual_doubt = True
            rule_id = "LOW_TRUST_BLOCK"

        # Verdict Event 생성 및 로깅
        if self.logger:
            verdict_result = emit_verdict(
                self.logger,
                trace_id=trace_id,
                decision=decision,
                rule_id=rule_id,
                trinity_score=trinity_score,
                risk_score=risk_score,
                dry_run_default=dry_run_default,
                residual_doubt=residual_doubt,
            )
            state["verdict_event"] = verdict_result

        # 상태 업데이트 (Enum.value로 문자열 저장)
        state["final_decision"] = decision.value if hasattr(decision, "value") else decision
        state["dry_run_recommended"] = dry_run_default
        state["residual_doubt"] = residual_doubt

        return state


def build_verdict_event(
    *,
    trace_id: str,
    decision: Decision,
    rule_id: str,
    trinity_score: float,
    risk_score: float,
    dry_run_default: bool,
    residual_doubt: bool,
    graph_node_id: str = "node_04_verdict",
    step: int = 41,
    extra: Mapping[str, Any] | None = None,
) -> VerdictEvent:
    flags: VerdictFlags = {
        "dry_run": bool(dry_run_default),
        "residual_doubt": bool(residual_doubt),
    }
    return VerdictEvent(
        trace_id=trace_id,
        graph_node_id=graph_node_id,
        step=int(step),
        decision=decision,
        rule_id=rule_id,
        trinity_score=float(trinity_score),
        risk_score=float(risk_score),
        flags=flags,
        timestamp=VerdictEvent.now_iso(),
        extra=extra,
    )


def emit_verdict(
    logger: VerdictLogger,
    *,
    trace_id: str,
    decision: Decision,
    rule_id: str,
    trinity_score: float,
    risk_score: float,
    dry_run_default: bool,
    residual_doubt: bool,
    graph_node_id: str = "node_04_verdict",
    step: int = 41,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ev = build_verdict_event(
        trace_id=trace_id,
        decision=decision,
        rule_id=rule_id,
        trinity_score=trinity_score,
        risk_score=risk_score,
        dry_run_default=dry_run_default,
        residual_doubt=residual_doubt,
        graph_node_id=graph_node_id,
        step=step,
        extra=extra,
    )
    return logger.emit(ev)
