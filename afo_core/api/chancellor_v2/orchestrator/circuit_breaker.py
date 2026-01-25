# Trinity Score: 94.0 (善 - System Stability)
"""Circuit Breaker Pattern for Strategist Protection.

Strategist 장애 격리 및 복구를 위한 회로 차단기.
연속 실패 시 자동으로 차단하고, 점진적으로 복구합니다.

AFO 철학:
- 善 (Goodness): 시스템 안정성 보호
- 孝 (Serenity): 우아한 장애 복구
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """회로 차단기 상태."""

    CLOSED = "closed"  # 정상 동작
    OPEN = "open"  # 차단됨 (즉시 실패)
    HALF_OPEN = "half_open"  # 테스트 중


@dataclass
class CircuitStats:
    """회로 통계."""

    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class CircuitBreakerConfig:
    """회로 차단기 설정."""

    failure_threshold: int = 3  # 연속 실패 임계값
    success_threshold: int = 2  # HALF_OPEN에서 CLOSED로 전환 성공 횟수
    timeout_seconds: float = 30.0  # OPEN 상태 유지 시간
    half_open_max_calls: int = 1  # HALF_OPEN에서 허용할 동시 호출 수


@dataclass
class CircuitBreaker:
    """Strategist용 회로 차단기.

    Usage:
        breaker = CircuitBreaker(pillar="truth")

        async with breaker.protect():
            result = await strategist.evaluate(ctx)

        # 또는 데코레이터 방식
        @breaker.wrap
        async def evaluate(ctx):
            ...
    """

    pillar: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    stats: CircuitStats = field(default_factory=CircuitStats)
    _half_open_calls: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        """초기화 후 처리."""
        self._lock = asyncio.Lock()

    @property
    def is_available(self) -> bool:
        """호출 가능 여부."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            return self._should_attempt_reset()
        if self.state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.config.half_open_max_calls
        return False

    def _should_attempt_reset(self) -> bool:
        """OPEN → HALF_OPEN 전환 시도 여부."""
        if self.stats.last_failure_time == 0:
            return True
        elapsed = time.time() - self.stats.last_failure_time
        return elapsed >= self.config.timeout_seconds

    async def record_success(self) -> None:
        """성공 기록."""
        async with self._lock:
            self.stats.successes += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self._half_open_calls -= 1
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    async def record_failure(self, error: Exception | None = None) -> None:
        """실패 기록."""
        async with self._lock:
            self.stats.failures += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self._half_open_calls -= 1
                self._transition_to(CircuitState.OPEN)
            elif self.stats.consecutive_failures >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

            if error:
                logger.warning(f"[CircuitBreaker:{self.pillar}] Failure recorded: {error}")

    def _transition_to(self, new_state: CircuitState) -> None:
        """상태 전환."""
        old_state = self.state
        self.state = new_state

        if new_state == CircuitState.CLOSED:
            self.stats.consecutive_failures = 0
            self._half_open_calls = 0

        logger.info(f"[CircuitBreaker:{self.pillar}] {old_state.value} → {new_state.value}")

    async def _pre_call(self) -> bool:
        """호출 전 검사. True면 진행, False면 차단."""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_calls = 1
                    return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            return False

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """회로 차단기 보호 하에 함수 호출.

        Args:
            func: 호출할 비동기 함수
            *args: 함수 인자
            fallback: 차단 시 폴백 함수
            **kwargs: 함수 키워드 인자

        Returns:
            함수 결과 또는 폴백 결과

        Raises:
            CircuitOpenError: 회로가 열려있고 폴백이 없을 때
        """
        if not await self._pre_call():
            if fallback:
                logger.info(f"[CircuitBreaker:{self.pillar}] Using fallback")
                return (
                    await fallback(*args, **kwargs)
                    if asyncio.iscoroutinefunction(fallback)
                    else fallback(*args, **kwargs)
                )
            raise CircuitOpenError(f"Circuit breaker for {self.pillar} is OPEN")

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure(e)
            if fallback:
                logger.info(f"[CircuitBreaker:{self.pillar}] Error occurred, using fallback")
                return (
                    await fallback(*args, **kwargs)
                    if asyncio.iscoroutinefunction(fallback)
                    else fallback(*args, **kwargs)
                )
            raise

    def get_status(self) -> dict[str, Any]:
        """현재 상태 반환."""
        return {
            "pillar": self.pillar,
            "state": self.state.value,
            "stats": {
                "failures": self.stats.failures,
                "successes": self.stats.successes,
                "consecutive_failures": self.stats.consecutive_failures,
                "consecutive_successes": self.stats.consecutive_successes,
            },
            "is_available": self.is_available,
        }


class CircuitOpenError(Exception):
    """회로가 열려있을 때 발생하는 예외."""

    pass


class StrategistCircuitBreakerManager:
    """Strategist별 Circuit Breaker 관리자.

    Usage:
        manager = StrategistCircuitBreakerManager()

        async def evaluate_with_protection(strategist, ctx):
            breaker = manager.get_breaker(strategist.PILLAR)
            return await breaker.call(
                strategist.evaluate,
                ctx,
                fallback=lambda c: heuristic_fallback(c)
            )
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        """관리자 초기화."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._default_config = config or CircuitBreakerConfig()

    def get_breaker(self, pillar: str) -> CircuitBreaker:
        """Pillar용 Circuit Breaker 조회 (없으면 생성)."""
        pillar_lower = pillar.lower()
        if pillar_lower not in self._breakers:
            self._breakers[pillar_lower] = CircuitBreaker(
                pillar=pillar_lower,
                config=self._default_config,
            )
        return self._breakers[pillar_lower]

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """모든 Circuit Breaker 상태 조회."""
        return {pillar: breaker.get_status() for pillar, breaker in self._breakers.items()}

    async def reset_all(self) -> None:
        """모든 Circuit Breaker 리셋."""
        for breaker in self._breakers.values():
            async with breaker._lock:
                breaker.state = CircuitState.CLOSED
                breaker.stats = CircuitStats()
                breaker._half_open_calls = 0
        logger.info("All circuit breakers reset to CLOSED")
