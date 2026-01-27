"""
Resilience Core Module (The Shield of Yi Sun-sin)
Provides Circuit Breaker and other stability patterns.
Implemented manually to avoid external dependencies.
"""

import logging
import time
from enum import Enum
from functools import wraps

logger = logging.getLogger("AFO.resilience")


class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    """
    Yi Sun-sin's Shield: Prevents cascading failures.
    Manual implementation of Circuit Breaker pattern.
    """

    def __init__(self, failure_threshold=3, recovery_timeout=60, name="default") -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.state = State.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0

    def call(self, func, *args, **kwargs) -> None:
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self._transition_to(State.HALF_OPEN)
            else:
                raise CircuitBreakerOpenException(f"Circuit {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == State.HALF_OPEN:
                self._transition_to(State.CLOSED)
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def _record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(
            f"🛡️ [SHIELD ALERT] Failure detected in {self.name}. Count: {self.failure_count}/{self.failure_threshold}"
        )

        if self.failure_count >= self.failure_threshold:
            self._transition_to(State.OPEN)

    def _transition_to(self, new_state) -> None:
        self.state = new_state
        if new_state == State.OPEN:
            logger.critical(
                f"🛡️ [SHIELD ACTIVE] Circuit {self.name} BROKEN! Blocking requests for {self.recovery_timeout}s."
            )
        elif new_state == State.CLOSED:
            self.failure_count = 0
            logger.info(f"🟢 [SHIELD STANDBY] Circuit {self.name} RECOVERED.")
        elif new_state == State.HALF_OPEN:
            logger.warning(f"🟡 [SHIELD TESTING] Circuit {self.name} HALF-OPEN. Probing.")

    def __call__(self, func) -> None:
        @wraps(func)
        def wrapper(*args, **kwargs) -> None:
            return self.call(func, *args, **kwargs)

        return wrapper


# Singleton instance for JulieService
julie_breaker = CircuitBreaker(name="JulieService", failure_threshold=5, recovery_timeout=30)
