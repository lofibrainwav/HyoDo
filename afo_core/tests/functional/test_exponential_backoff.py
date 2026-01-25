# Trinity Score: 95.0 (Phase 29B Exponential Backoff Functional Tests)


def test_exponential_backoff_class() -> None:
    """Verify ExponentialBackoff class in AFO/exponential_backoff.py."""
    from AFO.exponential_backoff import ExponentialBackoff

    backoff = ExponentialBackoff(max_retries=2, base_delay=0.01, jitter=False)

    def success_func(x) -> None:
        return x + 1

    assert backoff.execute(success_func, 10) == 11
    assert backoff.total_successes == 1


def test_exponential_backoff_retry() -> None:
    """Verify retry logic in ExponentialBackoff."""
    from AFO.exponential_backoff import ExponentialBackoff

    backoff = ExponentialBackoff(max_retries=3, base_delay=0.01, jitter=False)

    def fail_and_success() -> None:
        if fail_and_success.count < 2:
            fail_and_success.count += 1
            raise ValueError("fail")
        return "success"

    fail_and_success.count = 0
    fail_and_success.__name__ = "fail_and_success"

    result = backoff.execute(fail_and_success)
    assert result == "success"
    assert backoff.total_attempts == 3
    assert backoff.total_successes == 1


async def test_async_exponential_backoff():
    """Verify async wrapper for exponential backoff."""
    from AFO.exponential_backoff import exponential_backoff

    async def async_success(x):
        return x * 2

    # max_retries must be positional OR passed after x
    result = await exponential_backoff(async_success, 2, 0.01, 2.0, 60.0, True, (Exception,), 10)
    assert result == 20
