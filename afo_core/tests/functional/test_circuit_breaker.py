# Trinity Score: 95.0 (Phase 29B Circuit Breaker Functional Tests)
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_full_flow():
    """Verify circuit breaker transitions and execution."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, service_name="test_service")

    async def fast_func(x):
        return x * 2

    # 1. Closed State Success
    result = await cb.call(fast_func, 10)
    assert result == 20
    assert cb.state == CircuitState.CLOSED
    assert cb.stats.successful_calls == 1

    # 2. Trigger Failure
    async def fail_func():
        raise ValueError("test failure")

    with pytest.raises(ValueError):
        await cb.call(fail_func)

    assert cb.stats.failed_calls == 1
    assert cb.state == CircuitState.CLOSED  # threshold not reached

    # 3. Trip to OPEN
    with pytest.raises(ValueError):
        await cb.call(fail_func)

    assert cb.state == CircuitState.OPEN
    assert cb.stats.failed_calls == 2

    # 4. Open State Rejection
    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(fast_func, 5)

    assert cb.stats.rejected_calls == 1

    # 5. Recovery to HALF_OPEN
    await asyncio.sleep(0.15)
    # This call should transition to HALF_OPEN then CLOSED on success
    result = await cb.call(fast_func, 5)
    assert result == 10
    assert cb.state == CircuitState.CLOSED
    assert cb.stats.successful_calls == 2


def test_circuit_breaker_status() -> None:
    """Verify status report content."""
    cb = CircuitBreaker(service_name="status_test")
    status = cb.get_status()
    assert status["service"] == "status_test"
    assert "state" in status
    assert "stats" in status
