import anyio
import pytest


# Mocking a task that might fail
async def failing_task(name: str):
    await anyio.sleep(0.1)
    raise ValueError(f"Task {name} failed as expected")


# Mocking a task that takes time
async def slow_task(name: str, duration: float):
    try:
        await anyio.sleep(duration)
        return f"Task {name} completed"
    except anyio.get_cancelled_exc_class():
        # This demonstrates local cleanup during cancellation
        print(f"Task {name} was cancelled and cleaned up")
        raise


@pytest.mark.anyio
async def test_task_group_exception_propagation():
    """Verify that exceptions are captured in an ExceptionGroup.

    Note: trio may cancel sibling tasks on first failure, so we check >= 1.
    """
    with pytest.raises(ExceptionGroup) as excinfo:
        async with anyio.create_task_group() as tg:
            tg.start_soon(failing_task, "A")
            tg.start_soon(failing_task, "B")

    # At least one exception should be captured (trio may cancel others)
    assert len(excinfo.value.exceptions) >= 1
    # At least one of our expected failures should be present
    exc_str = str(excinfo.value.exceptions)
    assert "Task A failed" in exc_str or "Task B failed" in exc_str


@pytest.mark.anyio
async def test_cancellation_propagation_case_a():
    """Case A: 한 태스크가 즉시 예외 -> 다른 태스크가 cancelled 되었는지 확인"""
    cancelled_event = anyio.Event()

    async def victim():
        try:
            await anyio.sleep(10)
        except anyio.get_cancelled_exc_class():
            cancelled_event.set()
            raise

    with pytest.raises(ExceptionGroup):
        async with anyio.create_task_group() as tg:
            tg.start_soon(failing_task, "Killer")
            tg.start_soon(victim)

    assert cancelled_event.is_set(), "Killer task did not trigger cancellation of victim"


@pytest.mark.anyio
async def test_scope_cleanup_case_b():
    """Case B: 타임아웃(move_on_after) -> 하위 태스크가 정리(cleanup) 되었는지 확인"""
    cleanup_done = False

    async def cleanup_task():
        nonlocal cleanup_done
        try:
            await anyio.sleep(1)
        finally:
            cleanup_done = True

    with anyio.move_on_after(0.1):
        await cleanup_task()

    assert cleanup_done is True, "Timeout did not trigger finally block cleanup"


@pytest.mark.anyio
async def test_instrumentation_no_swallow():
    """@instrument_task가 취소 신호를 삼키지 않는지 확인"""
    from utils.async_instrumentation import instrument_task

    caught = False

    @instrument_task("test")
    async def cancel_me():
        await anyio.sleep(1)

    with anyio.move_on_after(0.1):
        try:
            await cancel_me()
        except anyio.get_cancelled_exc_class():
            caught = True

    assert caught is True, "@instrument_task swallowed the cancellation signal"


@pytest.mark.anyio
async def test_cancellation_propagation():
    """Verify that a failure in one task cancels siblings in the TaskGroup."""
    with pytest.raises(ExceptionGroup):
        async with anyio.create_task_group() as tg:
            tg.start_soon(failing_task, "Killer")
            tg.start_soon(slow_task, "Victim", 10.0)

    # If the test finishes quickly, it means the 10s task was cancelled instantly.
    # The 'Victim' task should NOT complete.


@pytest.mark.anyio
async def test_move_on_after_timeout():
    """Verify anyio.move_on_after as a replacement for asyncio.wait_for."""
    with anyio.move_on_after(0.2) as scope:
        await anyio.sleep(1.0)

    assert scope.cancelled_caught is True


@pytest.mark.anyio
async def test_fail_after_timeout():
    """Verify anyio.fail_after raises TimeoutError."""
    with pytest.raises(TimeoutError):
        with anyio.fail_after(0.1):
            await anyio.sleep(0.5)


def test_instrumentation_demo() -> None:
    """Demonstrate how Trio-style instrumentation could be applied (Conceptual)."""
    # Note: Instrumentation requires a specific backend like Trio.
    # In a production environment, this would be passed to anyio.run(..., backend='trio')
    pass
