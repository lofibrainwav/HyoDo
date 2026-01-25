import logging
import os
from dataclasses import dataclass, field
from typing import Any

import anyio
import httpx

from AFO.utils.standard_shield import shield

# AFO Kingdom specific imports
# Telemetry configuration (Phase 79 - TODO-004)
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
TELEMETRY_ENABLED = os.getenv("TELEMETRY_ENABLED", "true").lower() == "true"

logger = logging.getLogger("afo.services.debugging_agent")


@dataclass
class AgentState:
    """Internal Model of the World (Belief State)"""

    entropy: float = 0.0  # Surprise/Free Energy
    known_errors: dict[str, int] = field(default_factory=dict)
    active_patches: list[str] = field(default_factory=list)
    last_observation_ts: float = 0.0


class HealingAgent:
    """
    2026 Debugging Super Agent (The Supervisor / 감찰관)
    Core Philosophy: Active Inference (Minimize Free Energy)
    """

    def __init__(self, name: str = "SimaYi_Healing_Bot") -> None:
        self.name = name
        self.state = AgentState()
        self.running = False
        self._action_queue = anyio.create_memory_object_stream(100)

    async def start(self) -> None:
        """Start the agent's structured concurrency lifecycle."""
        self.running = True
        logger.info(f"🛡️ [HealingAgent] {self.name} waking up for duty.")

        async with anyio.create_task_group() as tg:
            tg.start_soon(self._observation_loop)
            tg.start_soon(self._reasoning_loop)
            tg.start_soon(self._action_loop)

            # Keep alive until stopped
            while self.running:  # noqa: ASYNC110
                await anyio.sleep(1)

        logger.info(f"💤 [HealingAgent] {self.name} entering stasis.")

    async def stop(self) -> None:
        self.running = False

    @shield(default_return=None, pillar="眞")
    async def _observation_loop(self) -> None:
        """
        Sensory Input: Read logs, metrics, and error streams.
        Minimizing 'Surprise' starts with accurate perception.
        """
        logger.info("👀 [HealingAgent] Observation systems online.")
        while self.running:
            # Mock Observation: Check for specific log patterns or simulated metric spikes
            # In production, this would poll Sentry/Prometheus or subscribe to an event bus
            await self._perceive_environment()
            await anyio.sleep(5)  # Tick rate

    @shield(default_return=None, pillar="眞")
    async def _reasoning_loop(self) -> None:
        """
        Active Inference: Update internal model based on observations.
        If entropy (surprise) is high, formulate an action to reduce it.
        """
        logger.info("🧠 [HealingAgent] Reasoning engine active.")
        while self.running:
            if self.state.entropy > 0.5:
                logger.warning(
                    f"⚠️ [HealingAgent] High Entropy detected ({self.state.entropy}). Formulating plan."
                )
                await self._formulate_action()
            await anyio.sleep(2)

    @shield(default_return=None, pillar="善")
    async def _action_loop(self) -> None:
        """
        Act on the world to bring it closer to the internal model (Expectation).
        """
        logger.info("⚔️ [HealingAgent] Action actuators ready.")
        receiver = self._action_queue[1]
        async with receiver:
            async for action in receiver:
                await self._execute_action(action)

    async def _perceive_environment(self) -> None:
        """Gather telemetry from Prometheus/monitoring systems (Phase 79 - TODO-004)."""
        if not TELEMETRY_ENABLED:
            return

        try:
            # Query Prometheus for error rate metrics
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Query: AFO error rate in last 5 minutes
                query = "sum(rate(afo_errors_total[5m])) or vector(0)"
                response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": query},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data.get("data", {}).get("result", [])
                        if results:
                            error_rate = float(results[0].get("value", [0, 0])[1])
                            # Update entropy based on error rate
                            self.state.entropy = min(error_rate * 10, 1.0)
                            if error_rate > 0.01:
                                logger.warning(
                                    f"⚠️ [HealingAgent] Elevated error rate detected: {error_rate:.4f}"
                                )

                # Query: Memory pressure
                mem_query = "afo_memory_usage_percent or vector(0)"
                mem_response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": mem_query},
                )

                if mem_response.status_code == 200:
                    mem_data = mem_response.json()
                    if mem_data.get("status") == "success":
                        mem_results = mem_data.get("data", {}).get("result", [])
                        if mem_results:
                            mem_usage = float(mem_results[0].get("value", [0, 0])[1])
                            if mem_usage > 85:
                                self.state.entropy = max(self.state.entropy, 0.7)
                                logger.warning(
                                    f"⚠️ [HealingAgent] High memory usage: {mem_usage:.1f}%"
                                )

        except httpx.ConnectError:
            # Prometheus not available - fallback to stable state
            logger.debug("[HealingAgent] Prometheus unavailable, assuming stable state")
        except Exception as e:
            logger.debug(f"[HealingAgent] Telemetry error (non-critical): {e}")

    async def _formulate_action(self) -> None:
        """Decide on the best move to minimize free energy."""
        # Simple rule-based policy for prototype
        # In 2026, this would be an LLM or Bayesian Network

        # Example: If we saw a DTZ005 error recently
        if "DTZ005" in self.state.known_errors:
            count = self.state.known_errors["DTZ005"]
            if count > 0:
                logger.info("💡 [HealingAgent] Hypothesis: Timezone Naive Usage detected.")
                sender = self._action_queue[0]
                await sender.send({"type": "SELF_HEAL", "target": "DTZ005"})
                # Reset entropy perception for this issue
                self.state.known_errors["DTZ005"] = 0
                self.state.entropy = 0.0

    @shield(default_return=None, pillar="善")
    async def _execute_action(self, action: dict[str, Any]) -> None:
        """Execute the planned action."""
        action_type = action.get("type")

        if action_type == "SELF_HEAL":
            target = action.get("target")
            logger.info(f"🩹 [HealingAgent] PROPOSAL: Self-Healing Patch for {target}")
            logger.info(
                "⚠️ [HealingAgent] AUTO-COMMIT BLOCKED by 2026 Sealing Protocol (Goodness Gate)."
            )
            # Simulation of patching (No file modification)
            await anyio.sleep(0.5)
            self.state.active_patches.append(target)
            logger.info(f"✅ [HealingAgent] Patch SIMULATED: {target}. Pending Human Review.")

    # --- External Triggers (for Testing) ---

    async def trigger_anomaly(self, error_code: str) -> None:
        """Inject an anomaly to test Active Inference."""
        logger.warning(f"🔥 [HealingAgent] Anomaly injected: {error_code}")
        self.state.known_errors[error_code] = self.state.known_errors.get(error_code, 0) + 1
        self.state.entropy = 0.9  # Spike entropy to trigger reasoning
