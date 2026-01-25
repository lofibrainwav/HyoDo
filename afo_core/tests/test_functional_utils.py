# Trinity Score: 95.0 (Phase 29B Functional Coverage)
"""Functional Tests - Utils and Exponential Backoff

Split from test_coverage_functional.py for 500-line rule compliance.
"""

import pytest

# =============================================================================
# Utils Exponential Backoff Functional Tests
# =============================================================================


def test_utils_exponential_backoff() -> None:
    """Verify ExponentialBackoff in utils/exponential_backoff.py."""
    from utils.exponential_backoff import ExponentialBackoff

    backoff = ExponentialBackoff(max_retries=2, base_delay=0.01)

    def dummy() -> None:
        return "ok"

    assert backoff.execute(dummy) == "ok"
    assert backoff.get_stats()["total_successes"] == 1


@pytest.mark.asyncio
async def test_utils_async_backoff():
    """Verify async exponential_backoff in utils/exponential_backoff.py."""
    from utils.exponential_backoff import exponential_backoff

    async def async_dummy(x):
        return x

    res = await exponential_backoff(async_dummy, 2, 0.01, 2.0, 60.0, True, (Exception,), 123)
    assert res == 123


# =============================================================================
# Circuit Breaker Tests (referenced in original file header)
# =============================================================================


def test_circuit_breaker_basic() -> None:
    """Verify CircuitBreaker in utils/circuit_breaker.py."""
    from utils.circuit_breaker import CircuitBreaker, CircuitState

    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
