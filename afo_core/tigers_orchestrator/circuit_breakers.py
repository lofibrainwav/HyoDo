"""
Circuit Breaker Pattern for Tiger Generals (5호장군)

Per-General Circuit Breaker with automatic failure detection,
recovery, and Cross-Pillar coordination.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class TigerCircuitBreaker:
    """5호장군별 Circuit Breaker"""

    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    timeout_seconds: float = 30.0
    failure_threshold: int = 3
    success_threshold: int = 2
    half_open_max_calls: int = 1
    half_open_calls: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def should_allow_call(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
        elif self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        return False

    async def record_success(self) -> None:
        async with self._lock:
            self.success_count += 1
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED

    async def record_failure(self, error: Exception) -> None:
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls -= 1

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"[CircuitBreaker:{self.name}] "
                    f"Circuit opened after {self.failure_count} failures"
                )

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "is_available": self.should_allow_call(),
        }


class CrossPillarCoordinator:
    """Cross-Pillar Coordinator for 5호장군"""

    def __init__(self, event_bus: Any) -> None:
        self.event_bus = event_bus
        self.breakers: dict[str, TigerCircuitBreaker] = {}

        for general in [
            "truth_guard",
            "goodness_gate",
            "beauty_craft",
            "serenity_deploy",
            "eternity_log",
        ]:
            self.breakers[general] = TigerCircuitBreaker(
                name=general, timeout_seconds=30.0, failure_threshold=3, success_threshold=2
            )
            logger.info(f"Created circuit breaker for {general}")

    async def execute_with_circuit_protection(
        self, general_name: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute with circuit breaker protection"""

        breaker = self.breakers[general_name]

        if not breaker.should_allow_call():
            logger.warning(f"[CrossPillar] {general_name} circuit is {breaker.state.value}")

            if "fallback" in kwargs:
                return kwargs["fallback"]()
            else:
                raise Exception(f"Circuit breaker for {general_name} is {breaker.state.value}")

        try:
            result = await func(*args, **kwargs)
            await breaker.record_success()
            return result
        except Exception as e:
            await breaker.record_failure(e)
            await self._broadcast_concern(general_name, str(e))

            if breaker.should_allow_call():
                return await func(*args, **kwargs)

            raise e

    async def _broadcast_concern(self, source: str, error: str) -> None:
        """Broadcast concern"""
        await self.event_bus.publish(
            source=source,
            target="ALL",
            message_type="CONCERN",
            content=f"Execution failure in {source}: {error}",
            priority="HIGH",
        )
        logger.info(f"[CrossPillar] Broadcast concern from {source} to ALL generals")

    def get_all_breaker_status(self) -> dict[str, Any]:
        """Get all circuit breaker status"""
        return {name: breaker.get_status() for name, breaker in self.breakers.items()}
