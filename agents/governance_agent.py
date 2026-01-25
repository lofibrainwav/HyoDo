# Trinity Score: 92.0 (Established by Chancellor)
"""Governance Agent Core (TICKET-097)
Policy adherence monitoring and bounded autonomy enforcement.

2026 Best Practices Implementation:
- Policy Adherence: Monitor actions against AFO Kingdom policies
- Bounded Autonomy: Enforce operational limits for all agents
- Escalation Path: Route high-stakes decisions to human oversight
- Audit Trail: Automatic logging of all governance decisions

Philosophy:
- 眞 (Truth): Verify all actions against SSOT policies
- 善 (Goodness): Prevent harmful or risky operations
- 美 (Beauty): Transparent and explainable decision-making
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk classification for governance decisions."""

    LOW = "low"  # Auto-approve
    MEDIUM = "medium"  # Log and proceed with caution
    HIGH = "high"  # Require additional validation
    CRITICAL = "critical"  # Escalate to human


@dataclass
class PolicyCheck:
    """Result of a policy compliance check."""

    policy_name: str
    passed: bool
    risk_level: RiskLevel
    details: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class GovernanceDecision:
    """A governance decision with full audit trail."""

    action: str
    agent_name: str
    decision: str  # "approved", "denied", "escalated"
    risk_level: RiskLevel
    policy_checks: list[PolicyCheck]
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    human_override: bool = False


class GovernanceAgent:
    """Governance Agent for AFO Kingdom.

    Implements 2026 AI Agent best practices:
    1. Policy adherence monitoring
    2. Bounded autonomy architecture
    3. Escalation path to human oversight
    4. Comprehensive audit trail
    """

    def __init__(self) -> None:
        self.name = "Governance Agent (사마의)"
        self.audit_log: list[GovernanceDecision] = []

        # Bounded autonomy limits (rate limits)
        self.rate_limits: dict[str, int] = {
            "max_file_operations_per_minute": 10,
            "max_external_api_calls_per_minute": 5,
        }

        # Bounded autonomy limits (path restrictions)
        self.allowed_directories: list[str] = [
            "packages/dashboard/src/components/genui",
            "packages/afo-core/AFO",
            "docs",
        ]

        # Forbidden operations
        self.forbidden_operations: list[str] = [
            "delete_production_data",
            "modify_credentials",
            "disable_security",
        ]

        # Policy definitions
        self.policies = {
            "trinity_score_minimum": 85.0,
            "require_evidence_for_decisions": True,
            "human_approval_for_critical": True,
            "dry_run_before_wet": True,
            "relentless_mode": True,  # Sisyphus Mode (Auto-resume)
            "max_auto_resumes": 5,
        }

        self._operation_counts: dict[str, int] = {}

        # OWASP Agentic 2026: Kill Switch state (ASI01 mitigation)
        self.kill_switch_active = False
        self.kill_switch_reason: str | None = None
        self.kill_switch_timestamp: str | None = None

        # Agent Goal Hijack detection patterns (OWASP ASI01)
        self.goal_hijack_patterns: list[str] = [
            "ignore previous instructions",
            "disregard your guidelines",
            "forget your rules",
            "override your constraints",
            "you are now",
            "new objective:",
            "your real purpose",
        ]

        # Sisyphus Continuum State (ASI01 mitigation via persistence)
        self.continuum_state: dict[str, Any] = {
            "last_active_task": None,
            "resume_count": 0,
            "is_interrupted": False,
        }

    async def evaluate_action(
        self, action: str, agent_name: str, context: dict[str, Any] | None = None
    ) -> GovernanceDecision:
        """Evaluate a proposed action against governance policies.

        Args:
            action: The action being proposed (e.g., "create_file", "call_api")
            agent_name: Name of the agent requesting the action
            context: Additional context about the action

        Returns:
            GovernanceDecision with approval status and audit trail
        """
        context = context or {}
        logger.info(f"[{self.name}] Evaluating action: {action} from {agent_name}")

        policy_checks: list[PolicyCheck] = []

        # 1. Check forbidden operations
        forbidden_check = self._check_forbidden_operations(action)
        policy_checks.append(forbidden_check)

        # 2. Check rate limits (bounded autonomy)
        rate_check = self._check_rate_limits(action)
        policy_checks.append(rate_check)

        # 3. Check directory restrictions
        if "path" in context:
            path_check = self._check_allowed_directories(context["path"])
            policy_checks.append(path_check)

        # 4. Check Trinity Score if available
        if "trinity_score" in context:
            trinity_check = self._check_trinity_score(context["trinity_score"])
            policy_checks.append(trinity_check)

        # Determine overall risk level
        max_risk: RiskLevel = max((c.risk_level for c in policy_checks), key=lambda x: x.value)
        all_passed = all(c.passed for c in policy_checks)

        # Make decision
        if max_risk == RiskLevel.CRITICAL:
            decision = "escalated"
            reasoning = "Critical risk action requires human approval"
        elif all_passed:
            decision = "approved"
            reasoning = "All policy checks passed"
        else:
            decision = "denied"
            failed_policies = [c.policy_name for c in policy_checks if not c.passed]
            reasoning = f"Failed policies: {', '.join(failed_policies)}"

        # Create governance decision
        gov_decision = GovernanceDecision(
            action=action,
            agent_name=agent_name,
            decision=decision,
            risk_level=max_risk,
            policy_checks=policy_checks,
            reasoning=reasoning,
        )

        # Log to audit trail
        self.audit_log.append(gov_decision)
        self._persist_audit_log(gov_decision)

        logger.info(f"[{self.name}] Decision: {decision} | Risk: {max_risk.value}")
        return gov_decision

    def _check_forbidden_operations(self, action: str) -> PolicyCheck:
        """Check if action is in forbidden list."""
        is_forbidden = action in self.forbidden_operations
        return PolicyCheck(
            policy_name="forbidden_operations",
            passed=not is_forbidden,
            risk_level=RiskLevel.CRITICAL if is_forbidden else RiskLevel.LOW,
            details=f"Action '{action}' {'is forbidden' if is_forbidden else 'is allowed'}",
        )

    def _check_rate_limits(self, action: str) -> PolicyCheck:
        """Check if rate limits are exceeded."""
        # Simplified rate limit check
        key = f"{action}_{datetime.now(UTC).strftime('%Y%m%d%H%M')}"
        current_count = self._operation_counts.get(key, 0)

        max_limit = self.rate_limits.get(f"max_{action}_per_minute", 100)
        is_within_limit = current_count < max_limit

        self._operation_counts[key] = current_count + 1

        return PolicyCheck(
            policy_name="rate_limits",
            passed=is_within_limit,
            risk_level=RiskLevel.MEDIUM if not is_within_limit else RiskLevel.LOW,
            details=f"Rate: {current_count + 1}/{max_limit}",
        )

    def _check_allowed_directories(self, path: str) -> PolicyCheck:
        """Check if path is in allowed directories."""
        allowed = any(path.startswith(allowed_dir) for allowed_dir in self.allowed_directories)
        return PolicyCheck(
            policy_name="directory_restrictions",
            passed=allowed,
            risk_level=RiskLevel.HIGH if not allowed else RiskLevel.LOW,
            details=f"Path '{path}' {'is allowed' if allowed else 'is restricted'}",
        )

    def _check_trinity_score(self, score: float) -> PolicyCheck:
        """Check if Trinity Score meets minimum threshold."""
        min_score = self.policies["trinity_score_minimum"]
        passed = score >= min_score
        return PolicyCheck(
            policy_name="trinity_score_minimum",
            passed=passed,
            risk_level=RiskLevel.MEDIUM if not passed else RiskLevel.LOW,
            details=f"Trinity Score: {score}/{min_score}",
        )

    def _persist_audit_log(self, decision: GovernanceDecision) -> None:
        """Persist audit log to file for compliance."""
        try:
            # Dynamic path calculation
            audit_dir = (
                Path(__file__).parent.parent.parent.parent.parent / "docs" / "ssot" / "audit"
            )
            audit_dir.mkdir(parents=True, exist_ok=True)

            audit_file = audit_dir / "governance_decisions.jsonl"

            import json
            from dataclasses import asdict

            with audit_file.open("a", encoding="utf-8") as f:
                # Convert dataclass to dict for JSON serialization
                entry = asdict(decision)
                entry["risk_level"] = decision.risk_level.value
                entry["policy_checks"] = [
                    {**asdict(pc), "risk_level": pc.risk_level.value}
                    for pc in decision.policy_checks
                ]
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist audit log: {e}")

    def get_audit_summary(self) -> dict[str, Any]:
        """Get summary of governance decisions."""
        total = len(self.audit_log)
        approved = sum(1 for d in self.audit_log if d.decision == "approved")
        denied = sum(1 for d in self.audit_log if d.decision == "denied")
        escalated = sum(1 for d in self.audit_log if d.decision == "escalated")

        return {
            "total_decisions": total,
            "approved": approved,
            "denied": denied,
            "escalated": escalated,
            "approval_rate": approved / total if total > 0 else 0,
        }

    async def request_human_override(
        self, decision: GovernanceDecision, justification: str
    ) -> GovernanceDecision:
        """Request human override for a denied or escalated decision.

        This is a placeholder for integration with human-in-the-loop systems.
        """
        logger.warning(
            f"[{self.name}] Human override requested for: {decision.action} "
            f"| Justification: {justification}"
        )

        # In production, this would integrate with approval workflows
        # For now, log the request and return the original decision
        decision.human_override = True
        return decision


# Singleton
governance_agent = GovernanceAgent()


async def evaluate_action(action: str, agent_name: str, **context: Any) -> GovernanceDecision:
    """Convenience function to evaluate an action through governance."""
    return await governance_agent.evaluate_action(action, agent_name, context)


# ===== OWASP Agentic 2026 Kill Switch API =====


def activate_kill_switch(reason: str) -> dict[str, Any]:
    """Activate emergency kill switch for all agents (OWASP ASI01).

    Args:
        reason: Reason for activation

    Returns:
        Status of kill switch activation
    """
    governance_agent.kill_switch_active = True
    governance_agent.kill_switch_reason = reason
    governance_agent.kill_switch_timestamp = datetime.now(UTC).isoformat()

    logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")

    return {
        "status": "activated",
        "reason": reason,
        "timestamp": governance_agent.kill_switch_timestamp,
    }


def deactivate_kill_switch(authorization_code: str) -> dict[str, Any]:
    """Deactivate kill switch (requires authorization).

    Args:
        authorization_code: Human authorization code

    Returns:
        Status of deactivation
    """
    # In production, would validate authorization_code
    if not authorization_code:
        return {"status": "error", "message": "Authorization required"}

    governance_agent.kill_switch_active = False
    prev_reason = governance_agent.kill_switch_reason
    governance_agent.kill_switch_reason = None

    logger.info(f"✅ Kill switch deactivated (was: {prev_reason})")

    return {
        "status": "deactivated",
        "previous_reason": prev_reason,
        "deactivated_at": datetime.now(UTC).isoformat(),
    }


def is_kill_switch_active() -> bool:
    """Check if kill switch is currently active."""
    return governance_agent.kill_switch_active


def get_kill_switch_status() -> dict[str, Any]:
    """Get current kill switch status."""
    return {
        "active": governance_agent.kill_switch_active,
        "reason": governance_agent.kill_switch_reason,
        "activated_at": governance_agent.kill_switch_timestamp,
    }


def detect_goal_hijack(input_text: str) -> dict[str, Any]:
    """Detect potential Agent Goal Hijack attempts (OWASP ASI01).

    Args:
        input_text: Text to analyze for hijack patterns

    Returns:
        Detection result with threat details
    """
    input_lower = input_text.lower()
    detected: list[str] = []

    for pattern in governance_agent.goal_hijack_patterns:
        if pattern in input_lower:
            detected.append(pattern)

    if detected:
        logger.warning(f"⚠️ Goal Hijack attempt detected: {detected}")
        return {
            "is_hijack_attempt": True,
            "patterns_found": detected,
            "threat_level": "HIGH",
            "recommendation": "Block input and log incident",
        }

    return {
        "is_hijack_attempt": False,
        "patterns_found": [],
        "threat_level": "NONE",
    }


def enforce_continuum() -> dict[str, Any]:
    """[Phase 50] Enforce task continuation (Sisyphus Mode).
    Ensures that if an agent stops, the system re-triggers it until DONE.
    """
    if not governance_agent.policies.get("relentless_mode"):
        return {"status": "disabled"}

    state = governance_agent.continuum_state
    if (
        state["is_interrupted"]
        and state["resume_count"] < governance_agent.policies["max_auto_resumes"]
    ):
        state["resume_count"] += 1
        logger.info(
            f"🔄 [Sisyphus] Resuming task: {state['last_active_task']} (Attempt {state['resume_count']})"
        )
        return {
            "status": "resuming",
            "task": state["last_active_task"],
            "attempt": state["resume_count"],
        }

    return {"status": "idle", "reason": "No pending interrupted tasks"}
