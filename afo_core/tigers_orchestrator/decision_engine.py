"""
Ambassador Pattern Decision Engine for Tiger Generals (5호장군)

Automated execution flows for AUTO_RUN/ASK_COMMANDER/BLOCK decisions.
Implements Ambassador pattern for separating business logic from execution.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .event_bus import TigerGeneralsEventBus
    from .models import DecisionAction
    from .scoring import TrinityScoreAggregator

logger = logging.getLogger(__name__)


class ActionExecutor(Protocol):
    """Action executor protocol"""

    async def execute(self, action: DecisionAction) -> dict[str, Any]:
        """Execute action"""
        pass


class TigerGeneralsAmbassador:
    """Ambassador pattern for 5호장군 decision execution"""

    def __init__(
        self, event_bus: TigerGeneralsEventBus, scoring_aggregator: TrinityScoreAggregator
    ) -> None:
        """Initialize ambassador"""
        self.event_bus = event_bus
        self.scoring = scoring_aggregator
        self.action_queue: list[dict[str, Any]] = []

    async def execute_auto_run(self, decision_context: dict[str, Any]) -> bool:
        """AUTO_RUN execution"""

        actions = []

        deploy_action = {
            "action_type": "DEPLOY",
            "target": "production",
            "payload": decision_context,
        }
        actions.append(deploy_action)

        log_action = {
            "action_type": "LOG_EVIDENCE",
            "target": "trinity_evidence",
            "payload": {
                "decision": "AUTO_RUN",
                "trinity_score": decision_context.get("trinity_score"),
                "risk_score": decision_context.get("risk_score"),
            },
        }
        actions.append(log_action)

        results = await self._execute_actions(actions)

        if results[0].get("success"):
            logger.info("[Ambassador] AUTO_RUN executed successfully")
            return True
        else:
            logger.warning("[Ambassador] AUTO_RUN failed, falling back to ASK_COMMANDER")
            await self.execute_ask_commander(decision_context)
            return False

    async def execute_ask_commander(self, decision_context: dict[str, Any]) -> None:
        """ASK_COMMANDER execution"""

        actions = []

        notify_action = {
            "action_type": "NOTIFY",
            "target": "commander",
            "payload": {
                "message": "승인 필요: Trinity Score " + str(decision_context.get("trinity_score")),
                "risk_score": decision_context.get("risk_score"),
                "action_required": "DEPLOY_APPROVAL",
            },
        }
        actions.append(notify_action)

        set_state_action = {
            "action_type": "SET_STATE",
            "target": "system",
            "payload": {
                "state": "AWAITING_APPROVAL",
                "since": decision_context.get("timestamp", ""),
            },
        }
        actions.append(set_state_action)

        await self._execute_actions(actions)
        logger.info("[Ambassador] ASK_COMMANDER executed - waiting for approval")

    async def execute_block(self, decision_context: dict[str, Any]) -> None:
        """BLOCK execution"""

        actions = []

        rollback_action = {
            "action_type": "ROLLBACK",
            "target": "deployment",
            "payload": {
                "reason": f"BLOCK Decision - Risk Score: {decision_context.get('risk_score')}",
                "rollback_to": "last_stable_version",
            },
        }
        actions.append(rollback_action)

        notify_action = {
            "action_type": "NOTIFY",
            "target": "commander",
            "payload": {
                "message": "배포 차단됨 - Risk Score: " + str(decision_context.get("risk_score")),
                "action_required": "MANUAL_INVESTIGATION",
            },
        }
        actions.append(notify_action)

        log_action = {
            "action_type": "LOG_EVIDENCE",
            "target": "trinity_evidence",
            "payload": {
                "decision": "BLOCK",
                "reason": "RISK_TOO_HIGH",
                "timestamp": decision_context.get("timestamp", ""),
            },
        }
        actions.append(log_action)

        await self._execute_actions(actions)
        logger.warning("[Ambassador] BLOCK executed - deployment prevented")

    async def _execute_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute list of actions"""
        results = []

        for action in actions:
            try:
                result = await self._execute_single_action(action)
                results.append(
                    {"action_type": action.get("action_type"), "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"action_type": action.get("action_type"), "success": False, "error": str(e)}
                )
                logger.error(f"[Ambassador] Action failed: {action.get('action_type')} - {e}")

        return results

    async def _execute_single_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute single action"""
        action_type = action.get("action_type")

        if action_type == "DEPLOY":
            return await self._deploy_action(action)
        elif action_type == "NOTIFY":
            return await self._notify_action(action)
        elif action_type == "SET_STATE":
            return await self._set_state_action(action)
        elif action_type == "ROLLBACK":
            return await self._rollback_action(action)
        elif action_type == "LOG_EVIDENCE":
            return await self._log_evidence_action(action)
        else:
            logger.warning(f"[Ambassador] Unknown action type: {action_type}")
            return {"action_type": action_type, "success": False}

    async def _deploy_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Deploy action"""
        logger.info("[Ambassador] Executing deploy to production")
        return {"action_type": "deploy", "status": "executed", "timestamp": action.get("timestamp")}

    async def _notify_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Notify action"""
        logger.info(
            f"[Ambassador] Notifying commander: {action.get('payload', {}).get('message', '')}"
        )
        return {"action_type": "notify", "status": "notified", "timestamp": action.get("timestamp")}

    async def _set_state_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Set state action"""
        logger.info(f"[Ambassador] Setting state: {action.get('payload', {}).get('state')}")
        return {"action_type": "set_state", "status": "set", "timestamp": action.get("timestamp")}

    async def _rollback_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Rollback action"""
        logger.info(
            f"[Ambassador] Rolling back deployment: {action.get('payload', {}).get('reason', '')}"
        )
        return {
            "action_type": "rollback",
            "status": "rolled_back",
            "timestamp": action.get("timestamp"),
        }

    async def _log_evidence_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Log evidence action"""
        logger.info(f"[Ambassador] Logging evidence: {action.get('payload', {})}")
        return {
            "action_type": "log_evidence",
            "status": "logged",
            "timestamp": action.get("timestamp"),
        }
