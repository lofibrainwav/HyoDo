from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

# Trinity Score: 90.0 (Established by Chancellor)
"""Circuit Breaker Pattern for AFO Kingdom
Prevents cascading failures by temporarily blocking calls to failing services.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service failing, requests blocked immediately
- HALF_OPEN: Testing recovery, limited requests allowed
"""


# 로깅 설정
logger = logging.getLogger(__name__)


T = TypeVar("T")


class CircuitState(Enum):
    """Circuit Breaker states."""

    CLOSED = "closed"  # Normal: requests pass through
    OPEN = "open"  # Failing: requests blocked
    HALF_OPEN = "half_open"  # Recovery: testing with limited requests


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    state_changes: int = 0


class CircuitBreaker:
    """Circuit Breaker implementation for async functions.

    Usage:
        circuit = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            service_name="ollama"
        )

        @circuit
        async def call_ollama(prompt: str):
            return await ollama_client.chat(prompt)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
        expected_exceptions: tuple[type[BaseException], ...] = (Exception,),
        service_name: str = "unknown",
        on_open: Callable[[CircuitBreaker], None] | None = None,
        on_close: Callable[[CircuitBreaker], None] | None = None,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exceptions = expected_exceptions
        self.service_name = service_name
        self.on_open = on_open
        self.on_close = on_close

        # Internal state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        self._stats = CircuitStats()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics."""
        return self._stats

    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has passed."""
        try:
            if self._last_failure_time is None:
                return False
            return time.time() - self._last_failure_time >= self.recovery_timeout
        except (TypeError, AttributeError) as e:
            logger.debug("복구 타임아웃 확인 실패 (타입/속성 에러): %s", str(e))
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("복구 타임아웃 확인 중 예상치 못한 에러: %s", str(e))
            return False

    def _record_success(self) -> None:
        """Record a successful call."""
        try:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.last_success_time = time.time()
        except (AttributeError, TypeError) as e:
            logger.debug("성공 기록 실패 (속성/타입 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("성공 기록 중 예상치 못한 에러: %s", str(e))

    def _record_failure(self) -> None:
        """Record a failed call."""
        try:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.last_failure_time = time.time()
            self._failure_count += 1
            self._last_failure_time = time.time()
        except (AttributeError, TypeError) as e:
            logger.debug("실패 기록 실패 (속성/타입 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("실패 기록 중 예상치 못한 에러: %s", str(e))

    def _trip(self) -> None:
        """Open the circuit breaker."""
        try:
            self._state = CircuitState.OPEN
            self._stats.state_changes += 1
            logger.warning(
                "[Circuit Breaker] %s: OPEN (연속 %d회 실패)",
                self.service_name,
                self._failure_count,
            )
            if self.on_open:
                self.on_open(self)
        except (AttributeError, TypeError) as e:
            logger.debug("Circuit Breaker 트립 실패 (속성/타입 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("Circuit Breaker 트립 중 예상치 못한 에러: %s", str(e))

    def _reset(self) -> None:
        """Close the circuit breaker."""
        try:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_calls = 0
            self._stats.state_changes += 1
            logger.info("[Circuit Breaker] %s: CLOSED (복구 완료)", self.service_name)
            if self.on_close:
                self.on_close(self)
        except (AttributeError, TypeError) as e:
            logger.debug("Circuit Breaker 리셋 실패 (속성/타입 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("Circuit Breaker 리셋 중 예상치 못한 에러: %s", str(e))

    async def _enter_half_open(self) -> None:
        """Transition to half-open state."""
        try:
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0
            self._stats.state_changes += 1
            logger.info("[Circuit Breaker] %s: HALF_OPEN (복구 시도 중)", self.service_name)
        except (AttributeError, TypeError) as e:
            logger.debug("Circuit Breaker HALF_OPEN 전환 실패 (속성/타입 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("Circuit Breaker HALF_OPEN 전환 중 예상치 못한 에러: %s", str(e))

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute a function through the circuit breaker."""
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    await self._enter_half_open()
                else:
                    self._stats.rejected_calls += 1
                    remaining = self.recovery_timeout - (
                        time.time() - (self._last_failure_time or 0)
                    )
                    raise CircuitBreakerOpenError(
                        f"[{self.service_name}] 서비스 일시 불가 (복구까지 {remaining:.0f}초)"
                    )

            # Check half-open call limit
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._stats.rejected_calls += 1
                    raise CircuitBreakerOpenError(
                        f"[{self.service_name}] 복구 테스트 진행 중 (잠시 대기)"
                    )
                self._half_open_calls += 1

        # Execute the call
        try:
            result = await func(*args, **kwargs)

            async with self._lock:
                self._record_success()
                if self._state == CircuitState.HALF_OPEN:
                    self._reset()

            return result

        except self.expected_exceptions:
            async with self._lock:
                self._record_failure()

                if self._state == CircuitState.HALF_OPEN:
                    # Failed during recovery - back to open
                    self._state = CircuitState.OPEN
                    print(f"❌ [Circuit Breaker] {self.service_name}: 복구 실패, 다시 OPEN")
                elif self._failure_count >= self.failure_threshold:
                    self._trip()

            raise

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator interface for the circuit breaker."""
        try:

            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await self.call(func, *args, **kwargs)

            # Attach circuit breaker info to the wrapper
            wrapper.circuit_breaker = self  # type: ignore[attr-defined]
            return wrapper
        except (AttributeError, TypeError) as e:
            logger.debug("Circuit Breaker 데코레이터 생성 실패 (속성/타입 에러): %s", str(e))
            return func
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("Circuit Breaker 데코레이터 생성 중 예상치 못한 에러: %s", str(e))
            return func

    def get_status(self) -> dict[str, Any]:
        """Get current status for monitoring."""
        try:
            return {
                "service": self.service_name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "stats": {
                    "total_calls": self._stats.total_calls,
                    "successful": self._stats.successful_calls,
                    "failed": self._stats.failed_calls,
                    "rejected": self._stats.rejected_calls,
                },
                "recovery_timeout": self.recovery_timeout,
                "time_until_reset": (
                    max(
                        0.0,
                        self.recovery_timeout - (time.time() - (self._last_failure_time or 0.0)),
                    )
                    if self._last_failure_time and self._state == CircuitState.OPEN
                    else None
                ),
            }
        except (AttributeError, TypeError, KeyError) as e:
            logger.debug("Circuit Breaker 상태 조회 실패 (속성/타입/키 에러): %s", str(e))
            return {"service": self.service_name, "state": "error"}
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("Circuit Breaker 상태 조회 중 예상치 못한 에러: %s", str(e))
            return {"service": self.service_name, "state": "error"}


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting calls."""

    pass


# Pre-configured circuit breakers for AFO Kingdom services
ollama_circuit = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60,
    service_name="ollama",
    expected_exceptions=(asyncio.TimeoutError, ConnectionError, Exception),
)

qdrant_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    service_name="qdrant",
    expected_exceptions=(asyncio.TimeoutError, ConnectionError),
)

redis_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=15,
    service_name="redis",
    expected_exceptions=(ConnectionError,),
)


# Convenience functions
def get_all_circuit_statuses() -> dict[str, Any]:
    """Get status of all circuit breakers."""
    try:
        return {
            "ollama": ollama_circuit.get_status(),
            "qdrant": qdrant_circuit.get_status(),
            "redis": redis_circuit.get_status(),
        }
    except (AttributeError, KeyError) as e:
        logger.debug("모든 Circuit Breaker 상태 조회 실패 (속성/키 에러): %s", str(e))
        return {}
    except Exception as e:  # - Intentional fallback for unexpected errors
        logger.debug("모든 Circuit Breaker 상태 조회 중 예상치 못한 에러: %s", str(e))
        return {}


def reset_all_circuits() -> None:
    """Reset all circuit breakers (for testing/manual recovery)."""
    try:
        for circuit in [ollama_circuit, qdrant_circuit, redis_circuit]:
            circuit._reset()
        logger.info("All circuit breakers reset")
    except (AttributeError, TypeError) as e:
        logger.debug("모든 Circuit Breaker 리셋 실패 (속성/타입 에러): %s", str(e))
    except Exception as e:  # - Intentional fallback for unexpected errors
        logger.debug("모든 Circuit Breaker 리셋 중 예상치 못한 에러: %s", str(e))
