from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Trinity Score: 90.0 (Established by Chancellor)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    failure_threshold: int
    reset_timeout_s: float
    half_open_limit: int

    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float | None = None
    half_open_attempts: int = 0

    def allow_probe(self, now: float) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.opened_at is None:
                self.opened_at = now
                return False
            if (now - self.opened_at) >= self.reset_timeout_s:
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
                self.consecutive_failures = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_attempts >= self.half_open_limit:
                self.state = CircuitState.OPEN
                self.opened_at = now
                return False
            self.half_open_attempts += 1
            return True

    def record_success(self) -> None:
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.opened_at = None
        self.half_open_attempts = 0

    def record_failure(self, now: float) -> None:
        self.consecutive_failures += 1
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.opened_at = now
            self.half_open_attempts = 0
            return

        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = now
            self.half_open_attempts = 0
